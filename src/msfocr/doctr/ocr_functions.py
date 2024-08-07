from datetime import datetime
import re

# from doctr.io import DocumentFile
# from doctr.models import ocr_predictor
# from img2table.document import Image
# from img2table.ocr import DocTR
import Levenshtein
import numpy as np
import pandas as pd
from PIL import Image, ExifTags


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


def get_word_level_content(model, doc):
    """
    Inputs a document to the OCR model and returns the result
    :param model: OCR model
    :param doc: Document (pdf, jpg, png)
    :return: result
    """
    res = model(doc)
    return res


def get_confidence_values(res):
    """
    Creates a dictionary with text recognized by OCR model as key and model's confidence for the text as the value.
    :param res: result obtained from doctTR OCR model
    :return: dictionary of { "text recognized" : confidence value } pairs
    """
    confidence_dict = {}
    for page in res.pages:
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    confidence_dict[word.value] = word.confidence
    return confidence_dict


def get_tabular_content(model, image, confidence_dict=None):
    """
    Runs the input image in the OCR model. Detects all tables and content within tables and stores results as
    a list of pandas dataFrames (table_df). Calculates confidence values for all detected values in table_df
    and stores it in a list of pandas dataFrames (confidence_df).
    :param model: OCR model
    :param image: Image to be tested (Image object from img2table package)
    :param confidence_dict: Dictionary of text-confidence values
    :return: Two dataframes, table_df and confidence_df
    """
    if confidence_dict is None:
        confidence_dict = {}
    extracted_tables = image.extract_tables(ocr=model,
                                            implicit_rows=False,
                                            borderless_tables=False,
                                            min_confidence=50)

    table_df = []
    for _, table in enumerate(extracted_tables):
        table_df.append(table.df)

    confidence_df = [pd.DataFrame(np.zeros(df.shape), columns=df.columns, index=df.index) for df in table_df]

    for idx in range(len(table_df)):
        array = table_df[idx].values
        for row in range(array.shape[0]):
            for col in range(array.shape[1]):
                confidence = 0
                count = 0
                if array[row][col] is not None:
                    words = re.split(r'[ \n]+', array[row][col])
                    for word in words:
                        if word in confidence_dict:
                            confidence += confidence_dict[word]
                            count += 1
                    if count != 0: 
                        confidence_df[idx].iloc[row, col] = confidence / count

    return table_df, confidence_df


def get_sheet_type(res):
    """
    Finds the type of the tally sheet (dataSet, orgUnit, period) from the result of OCR model, where
    dataSet is the name of the dataset.
    orgUnit is the name of the organization unit where the data was taken.
    period is list of start and end dates detected.
    :param res: Result of OCR model
    :return: List of dataSet, orgUnit, period.
    """
    dataSet_list = ["RHGynobs - outpatient (resident/displaced)", "Vaccination - paediatric", "Vaccination - other preventive"]
    orgUnit_list = ["W-14"]

    max_similarity_dataSet = 0
    max_similarity_orgUnit = 0
    dataSet = ""
    orgUnit = ""
    period = []
    for page in res.pages:
        for block in page.blocks:
            for line in block.lines:
                text = " ".join(word.value for word in line.words)
                for name in dataSet_list:
                    sim = letter_by_letter_similarity(text, name)
                    if max_similarity_dataSet < sim:
                        max_similarity_dataSet = sim
                        dataSet = name
                for name in orgUnit_list:
                    sim = letter_by_letter_similarity(text, name)
                    if max_similarity_orgUnit < sim:
                        max_similarity_orgUnit = sim
                        orgUnit = name
                date = get_yyyy_mm_dd(text)
                if date is not None:
                    period.append(date)
    return [dataSet, orgUnit, sorted(period)]

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
            if cell_value is not None and cell_value!="-" and cell_value!="" and cell_value!="None":
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

def correct_image_orientation(image_path):
    """
    Corrects the orientation of an image based on its EXIF data.

    Usage:
    corrected_image = correct_image_orientation("path/to/image.jpg")

    :param image_path: The path to the image file.
    :return: PIL.Image.Image: The image with corrected orientation.
    """
    with Image.open(image_path) as image: 
        orientation = None
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = dict(image.getexif().items())
            if exif.get(orientation) == 3:
                image = image.rotate(180, expand=True)
            elif exif.get(orientation) == 6:
                image = image.rotate(270, expand=True)
            elif exif.get(orientation) == 8:
                image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass
        return image.copy()

# ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
# document = DocumentFile.from_images("IMG_20240514_090947.jpg")
# result = get_word_level_content(ocr_model, document)

# sheet_type = get_sheet_type(result)
# confidence_lookup_dict = get_confidence_values(result)

# doctr_ocr = DocTR(detect_language=False)
# img = Image(src="IMG_20240514_090947.jpg")  # , detect_rotation=True
# table_df, confidence_df = get_tabular_content(doctr_ocr, img, confidence_lookup_dict)
#
# dataElement_list = ['Paed (0-59m) vacc target population', 'BCG', 'HepB (birth dose, within 24h)',
#                     'HepB (birth dose, 24h or later)',
#                     'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)', 'Polio (OPV) 2', 'Polio (OPV) 3',
#                     'Polio (IPV)', 'DTP+Hib+HepB (pentavalent) 1', 'DTP+Hib+HepB (pentavalent) 2',
#                     'DTP+Hib+HepB (pentavalent) 3']
#
# categoryCombo_list = ['0-11m', '12-59m', '5-14y']
#
# # Correct names
# for table in table_df:
#     for row_index in range(table.shape[0]):
#         row_name = table.iloc[row_index, 0]
#         max_similarity = 0
#         if row_name is not None:
#             for name in dataElement_list:
#                 sim = letter_by_letter_similarity(row_name, name)
#                 if max_similarity < sim:
#                     max_similarity = sim
#                     table.iloc[row_index, 0] = name

# from msfocr.data import data_upload_DHIS2

# data_upload_DHIS2.configure_DHIS2_server()
# df = pd.DataFrame({
#         '0': ['Paed (0-59m) vacc target population'],
#         '0-11m': [1],
#         '12-59m': [12],
#         '5-14y': [30]
#     })
# df1 = pd.DataFrame({
#         '0': ['BCG', 'HepB (birth dose, within 24h)', 'HepB (birth dose, 24h or later)', 'Polio (OPV) 0 (birth dose)', 
#               'Polio (OPV) 1 (from 6 wks)', 'Polio (OPV) 2', 'Polio (OPV) 3', 'Polio (IPV)', 'DTP+Hib+HepB (pentavalent) 1', 
#               'DTP+Hib+HepB (pentavalent) 2', 'DTP+Hib+HepB (pentavalent) 3'],
#         '0-11m': ['45+29', 1, '30+18', 1, 5, 2, 3,4,5,6,7],
#         '12-59m': [None, None, '55+29', 4,5,6,7,8,9,10,11],
#         '5-14y': [None, None, None, 4,5,6,7,8,9,10,'11'],
#     })

# print(len(generate_key_value_pairs(df1)))

# df = pd.DataFrame({
#         '0': ['BCG', 'HepB (birth dose, within 24h)', 'HepB (birth dose, 24h or later)',
#               'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)'],
#         '0-11m': ['45+29', None, None, None, None],
#         '12-59m': [None, None, '5', None, None],
#         '5-14y': [None, None, None, '6', None]
#     })
# print(df)
# a,b,c = generate_key_value_pairs(df, 'TgsFGeESrGz')
# print(a)
# print(b)
# print(c)

