from datetime import datetime

import Levenshtein
from simpleeval import simple_eval


def letter_by_letter_similarity(text1, text2):
    """
    Checks the letter by letter similarity between two strings
    :param text1: first text
    :param text2: second text
    :return: returns an integer between 0-1, 0 indicates no similarity, 1 indicates identical strings
    """
    # Calculate Levenshtein distance
    distance = Levenshtein.distance(text1, text2)

    # Calculate maximum possible length
    max_len = max(len(text1), len(text2))

    # Convert distance to similarity
    similarity = 1 - (distance / max_len)

    return similarity


def get_yyyy_mm_dd(text):
    """
    Checks if the input text is a date by comparing it with various known formats and returns date in unified YYYY-MM-DD format.
    :param text: String
    :return: Date in YYYY-MM-DD format or None
    """
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y", "%Y/%m/%d"]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(text, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None  # Return None if text is not a valid date in any format


def generate_key_value_pairs(table, form):
    """
    Generates key-value pairs in the format required to upload data to DHIS2.
    {'dataElement': data_element_id,
     'categoryOptionCombo': category_id,
     'value': cell_value}
     UIDs like data_element_id, category_id are obtained by querying the DHIS2 metadata.
    :param table: DataFrame generated from table detection
    :return: List of key value pairs as shown above.
    """ 
    data_element_pairs = []

    # Iterate over each cell in the DataFrame
    table_array = table.values
    columns = table.columns
    for row_index in range(table_array.shape[0]):
        # Row name in tally sheet
        data_element = table_array[row_index][0]
        for col_index in range(1, table_array.shape[1]):
            # Column name in tally sheet
            category = columns[col_index]
            cell_value = table_array[row_index][col_index]
            if cell_value is not None and cell_value!="-" and cell_value!="":
                data_element_id = None
                category_id = None
                # Search for the string in the "label" field of form information
                string_search = data_element + " " + category
                for group in form['groups']:
                    for field in group['fields']:
                        if field['label']==string_search:
                            data_element_id = field['dataElement']
                            category_id = field['categoryOptionCombo']
                
                # The following exceptions will be raised if the row or column name in the tally sheet is different from the names used in metadata
                # For eg. Pop1: Resident is called Population 1 in metadata
                # If this exception is raised the only way forward is for the user to manually change the row/column name to the one used in metadata
                if data_element_id is None or category_id is None:
                    raise Exception(f"Unable to find {string_search} in DHIS2 metadata")
                # Append to the list of data elements to be push to DHIS2
                data_element_pairs.append(
                    {"dataElement": data_element_id,
                    "categoryOptionCombo": category_id,
                    "value": cell_value}
                    )

    return data_element_pairs

            
def evaluate_cells(table_dfs):
    """Uses simple_eval to perform math operations on each cell, defaulting to input if failed.

    Args:
        table_dfs (_List_): List of table data frames

    Returns:
        _List_: List of table data frames
    """
    for table in table_dfs:
        print(table)
        table_removed_labels = table.iloc[1:, 1:]
        print(table_removed_labels)
        for col in table_removed_labels.columns:
            try:
                # Contents should be strings in order to be editable later
                table_removed_labels[col] = table_removed_labels[col].apply(lambda x: simple_eval(x) if x and x != "-" else x).astype("str")
            except Exception:
                continue
        print(table)
        print(table_removed_labels)
        table.update(table_removed_labels)
    return table_dfs