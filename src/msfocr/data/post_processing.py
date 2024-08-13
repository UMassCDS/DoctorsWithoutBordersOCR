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


def evaluate_cells(table_dfs):
    """Uses simple_eval to perform math operations on each cell, defaulting to input if failed.

    Args:
        table_dfs (_List_): List of table data frames

    Returns:
        _List_: List of table data frames
    """
    for table in table_dfs:
        table_removed_labels = table.iloc[1:, 1:]
        for col in table_removed_labels.columns:
            try:
                # Contents should be strings in order to be editable later
                table_removed_labels[col] = table_removed_labels[col].apply(lambda x: simple_eval(x) if x and x != "-" else x).astype("str")
            except Exception:
                continue
        table.update(table_removed_labels)
    return table_dfs

def clean_up(table_dfs):
    """Cleans up values in table that are returned as the string "None" by OCR model into empty string "" 

    Args:
        table_dfs (_List_): List of table data frames

    Returns:
        _List_: List of table data frames
    """
    for table in table_dfs:
        for row in range(table.shape[0]):
            for col in range(table.shape[1]):
                cell_value = table.iloc[row][col]
                if cell_value is None or cell_value=="None":
                    table.iloc[row][col] = ""            
    return table_dfs