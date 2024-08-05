import copy
from datetime import date
import json
import os

from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image
from img2table.ocr import DocTR
from PIL import Image as PILImage, ExifTags
import requests
import streamlit as st

from msfocr.data import dhis2
from msfocr.data import ocr_functions

def configure_secrets():
    """Checks that necessary environment variables are set for fast failing.
    Configures the DHIS2 server connection.
    """
    username = os.environ["DHIS2_USERNAME"]
    password = os.environ["DHIS2_PASSWORD"]
    server_url = os.environ["DHIS2_SERVER_URL"]
    dhis2.configure_DHIS2_server(username, password, server_url)

# Function definitions
@st.cache_data
def data_values(df):
    """
    Converts data from tables into key-value pairs 
    """
    data_values = []
    columns = df.columns.tolist()
    for col, i in df.iterrows():
        for cell in columns:
            if i[cell] is not None:
                new_cell = {"dataElement": f"{col}/{cell}", "value": f"{i[cell]}"}
                data_values.append(new_cell)
    return data_values


@st.cache_data
def dhis2_all_UIDs(item_type, search_items):
    """
    Gets all fields similar to search_items from the metadata
    :param item_type: Defines the type of metadata (dataset, organisation unit, data element) to search
           search_items: A list of text to search
           dhis2_username, dhis2_password, DHIS2_Test_Server_URL: DHIS2 login credentials
    :return A list of all (name,id) pairs of fields that match the search words       
    """
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items)


# def convert_df(dfs):
#     """
#     Converts tabular data recognized into json format required to upload data into DHIS2
#     :param Data as dataframes
#     :return Data in json format with form identification information
#     """
#     json_export = {}
#     if data_set == "":
#         data_set_id = ""
#     else:
#         data_set_id = dict(data_set_options)[data_set]
#     json_export["dataSet"] = f"{data_set_id}"
#     json_export["period"] = f"{period_start}P7D"
#     if org_unit == "":
#         org_unit_id = ""
#     else:
#         org_unit_id = dict(org_unit_options)[org_unit_dropdown]
#     json_export["orgUnit"] = f"{org_unit_id}"
#     data_values_list = []
#     for df in dfs:
#         data_values_list += data_values(df)
#     json_export["dataValues"] = data_values_list
#     return json.dumps(json_export)

def json_export(kv_pairs):
    """
    Converts tabular data recognized into json format required to upload data into DHIS2
    :param Data as dataframes
    :return Data in json format with form identification information
    """
    json_export = {}
    if org_unit_dropdown is None:
        raise ValueError("Please select organisation unit")
    if data_set == "":
        raise ValueError("Please select data set")
    json_export["dataSet"] = data_set_selected_id
    json_export["period"] = get_period()
    json_export["orgUnit"] = org_unit_child_id
    json_export["dataValues"] = kv_pairs
    return json.dumps(json_export)

def correct_field_names(dfs):
    """
    Corrects the text data in tables by replacing with closest match among the hardcoded fieldnames
    :param Data as dataframes
    :return Corrected data as dataframes
    """
    dataElement_list = ['', 'Paed (0-59m) vacc target population', 'BCG', 'HepB (birth dose, within 24h)',
            'HepB (birth dose, 24h or later)',
            'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)', 'Polio (OPV) 2', 'Polio (OPV) 3',
            'Polio (IPV)', 'DTP+Hib+HepB (pentavalent) 1', 'DTP+Hib+HepB (pentavalent) 2',
            'DTP+Hib+HepB (pentavalent) 3', 'DTP, TD, Td or TT booster', 'Measles 0', 'Measles 1',
            'Measles 2', 'MMR 0', 'MMR 1', 'MMR 2', 'PCV 1', 'PCV 2', 'PCV 3', 'PCV booster']
    categoryOptionsList = ['', '0-11m', '12-59m', '5-14y']
    
    for table in dfs:
        for row in range(table.shape[0]):
            max_similarity_dataElement = 0
            dataElement = ""
            text = table.iloc[row,0]
            if text is not None:
                for name in dataElement_list:
                    sim = ocr_functions.letter_by_letter_similarity(text, name)
                    if max_similarity_dataElement < sim:
                        max_similarity_dataElement = sim
                        dataElement = name
                table.iloc[row,0] = dataElement

    for table in dfs:
        for id,col in enumerate(table.columns):
            max_similarity_catOpt = 0
            catOpt = ""
            text = table.iloc[0,id]
            if text is not None:
                for name in categoryOptionsList:
                    sim = ocr_functions.letter_by_letter_similarity(text, name)
                    if max_similarity_catOpt < sim:
                        max_similarity_catOpt = sim
                        catOpt = name
                table.iloc[0,id] = catOpt
    return dfs        

# Function to set the first row as header
def set_first_row_as_header(df):
    """
    Sets the first row in the recognized table (ideally the header information for each column) as the table header
    :param Dataframe
    :return Dataframe after correction
    """
    df.columns = df.iloc[0]  
    df = df.iloc[1:]  
    df.reset_index(drop=True, inplace=True)  
    # print(df)
    return df

@st.cache_data
def get_uploaded_images(tally_sheet):
    """
    List of images uploaded by user as docTR DocumentFiles
    :param Files uploaded by user
    :return List of images uploaded by user as docTR DocumentFiles
    """
    return [DocumentFile.from_images(sheet.read()) for sheet in tally_sheet]

@st.cache_data
def get_results(uploaded_images):
    return [ocr_functions.get_word_level_content(ocr_model, doc) for doc in uploaded_images]

@st.cache_data
def get_tabular_content_wrapper(_doctr_ocr, img, confidence_lookup_dict):
    return ocr_functions.get_tabular_content(_doctr_ocr, img, confidence_lookup_dict)

def get_sheet_type_wrapper(result):
    return ocr_functions.get_sheet_type(result)

@st.cache_data
def get_data_sets(data_set_uids):
    return dhis2.getDataSets(data_set_uids)

@st.cache_data
def get_org_unit_children(org_unit_id):
    return dhis2.getOrgUnitChildren(org_unit_id)

@st.cache_resource
def create_ocr():
    """
    Load docTR ocr model and img2table docTR model  
    """
    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    doctr_ocr = DocTR(detect_language=False)
    return ocr_model, doctr_ocr

@st.cache_data
def correct_image_orientation(image_path):
    """
    Corrects the orientation of an image based on its EXIF data.
    Parameters:
    image_path (str): The path to the image file.
    Returns:
    PIL.Image.Image: The image with corrected orientation.
    """
    image = PILImage.open(image_path)
    orientation = None
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        if exif.get(orientation) == 3:
            image = image.rotate(180, expand=True)
        elif exif.get(orientation) == 6:
            image = image.rotate(270, expand=True)
        elif exif.get(orientation) == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

def week1_start_ordinal(year):
    jan1 = date(year, 1, 1)
    jan1_ordinal = jan1.toordinal()
    jan1_weekday = jan1.weekday()
    week1_start_ordinal = jan1_ordinal - ((jan1_weekday + 1) % 7)
    return week1_start_ordinal

def week_from_date(date_object):
    date_ordinal = date_object.toordinal()
    year = date_object.year
    week = ((date_ordinal - week1_start_ordinal(year)) // 7) + 1
    if week >= 52:
        if date_ordinal >= week1_start_ordinal(year + 1):
            year += 1
            week = 1
    return year, week

def get_period():
    year, week = week_from_date(period_start)
    return PERIOD_TYPES[period_type].format(
        year = year,
        day = period_start.day,
        month = period_start.month,
        week = week
        )

# Set the page layout to centered
# st.set_page_config(layout="wide")

# Initiation
if 'upload_key' not in st.session_state: 
    st.session_state['upload_key'] = 1000

# Initial Display
st.title("MSF OCR Tool")
st.write("### File Upload ###")
tally_sheet = st.file_uploader("Please upload one or more images of a tally sheet", type=["png", "jpg", "jpeg"],
                               accept_multiple_files=True,
                               key=st.session_state['upload_key'])

# Displaying images so the user can see them
with st.expander("Show Images"):
    for sheet in tally_sheet:
        rotated_image = correct_image_orientation(sheet)
        st.image(rotated_image)

# OCR Model
ocr_model, doctr_ocr = create_ocr()
configure_secrets()

# Hardcoded Periods, probably won't update but can get them through API
PERIOD_TYPES = {
    "Daily": "{year}{month}{day}",
    "Weekly": "{year}W{week}",
    "WeeklyWednesday": "{year}WedW{week}",
    "WeeklyThursday": "{year}ThuW{week}",
    "WeeklySaturday": "{year}SatW{week}",
    "WeeklySunday": "{year}SunW{week}",
    "BiWeekly": "{year}Bi{week}",
    "Monthly": "{year}{month}",
    "BiMonthly": "{year}{month}B",
    "Quarterly": "{year}{quarter_number}",
    "SixMonthly": "{year}{semiyear_number}",
    "SixMonthlyApril": "{year}April{semiyear_number}",
    "SixMonthlyNovember": "{year}Nov{semiyear_number}",
    "Yearly": "{year}",
    "FinancialApril": "{year}April",
    "FinancialJuly": "{year}July",
    "FinancialOct": "{year}Oct",
    "FinancialNov": "{year}Nov",
}

# Once images are uploaded
if len(tally_sheet) > 0:    
    
    if st.button("Clear Form") and 'upload_key' in st.session_state.keys():
        st.session_state.upload_key += 1
        if 'table_dfs' in st.session_state:
            del st.session_state['table_dfs']
        st.rerun()
        
    uploaded_images = get_uploaded_images(tally_sheet)
    results = get_results(uploaded_images)
    
    ### CORRECT THIS TO ALLOW PROCESSING OF ALL IMAGES
    # ***************************************
    image = uploaded_images[0]
    result = results[0]
    # ***************************************

    # form_type looks like [dataSet, orgUnit, period=[startDate, endDate]]
    form_type = get_sheet_type_wrapper(result)
    
    # Initialize org_unit with any recognized text from tally sheet
    # Change the value when user edits the field
    if form_type[1]:
        org_unit = st.text_input("Organisation Unit", value=form_type[1])    
    else: 
        org_unit = st.text_input("Organisation Unit", placeholder="Search organisation unit name")
    
    # Get all UIDs corresponding to the text field value 
    if org_unit:
        org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit])
        org_unit_dropdown = st.selectbox(
            "Organisation Results",
            [id[0] for id in org_unit_options],
            index=None
        )
    
    # Get org unit children    
    if org_unit_dropdown is not None:
        org_unit_id = [id[1] for id in org_unit_options if id[0] == org_unit_dropdown][0]
        org_unit_children_options = get_org_unit_children(org_unit_id)
        org_unit_children_dropdown = st.selectbox(
            "Organisation Children",
            sorted([id[0] for id in org_unit_children_options]),
            index=None
        )
        
        if org_unit_children_dropdown is not None:
            
            org_unit_child_id = [id[2] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
            data_set_ids = [id[1] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
            data_set_options = get_data_sets(data_set_ids)
            data_set = st.selectbox(
                "Data Set",
                sorted([id[0] for id in data_set_options]),
                index=None
            )
            
            if data_set is not None:
                data_set_selected_id = [id[1] for id in data_set_options if id[0] == data_set][0]
                period_type = [id[2] for id in data_set_options if id[0] == data_set][0]
                st.write("Period Type\: " + period_type)

    # Same as org_unit
    # if form_type[0]:
    #     data_set = st.text_input("Data Set", value=form_type[0])
    # else:
    #     data_set = st.text_input("Data Set", placeholder="Search data set name")

    # if data_set:            
    #     data_set_options = dhis2_all_UIDs("dataSets", [data_set])
    #     data_set_dropdown = st.selectbox(
    #         "Searched Datasets",
    #         [id[0] for id in data_set_options],
    #         index=None
    #     )

    # Initialize with period values recognized from tally sheet or entered by user    
    
    if form_type[2]:
        if form_type[2][0]:    
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", value=form_type[2][0])
        else:
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD") 
        # if form_type[2][1]:    
        #     period_end = st.date_input("Period End Date", format="YYYY-MM-DD", value=form_type[2][1])
        # else:
        #     period_end = st.date_input("Period End Date", format="YYYY-MM-DD")        
    else:
        period_start = st.date_input("Period Start Date", format="YYYY-MM-DD")
        # period_end = st.date_input("Period End Date", format="YYYY-MM-DD")


    # Populate streamlit with data recognized from tally sheets
    for result in results:
        # Get tabular data ad dataframes
        confidence_lookup_dict = ocr_functions.get_confidence_values(result)
        table_dfs = []
        for sheet in tally_sheet:
            img = Image(src=sheet)
            table_df, confidence_df = get_tabular_content_wrapper(doctr_ocr, img, confidence_lookup_dict)
            table_dfs += table_df

            # Store table data in session state
            if 'table_dfs' not in st.session_state:
                st.session_state.table_dfs = table_dfs

            # print(table_dfs)

            # Displaying the editable information
            for i, df in enumerate(st.session_state.table_dfs):
                st.write(f"Table {i+1}")
    
                col1, col2 = st.columns([4, 1]) 
                
                with col1:
                    # Display tables as editable fields
                    table_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}")
                
                with col2:
                    # Add column functionality
                    new_col_name = st.text_input("New column name", key=f"new_col_{i}")
                    if st.button("Add Column", key=f"add_col_{i}"):
                        if new_col_name:
                            table_dfs[i][new_col_name] = None

                    # Delete column functionality
                    if not table_dfs[i].empty:
                        col_to_delete = st.selectbox("Column to delete", table_dfs[i].columns, key=f"del_col_{i}")
                        if st.button("Delete Column", key=f"delete_col_{i}"):
                            table_dfs[i] = table_dfs[i].drop(columns=[col_to_delete])

            # Button that when clicked corrects the row and column indices of table with best match 
            if st.button("Correct field names", key="correct_names"):
                table_dfs = correct_field_names(table_dfs)   

            # Rerun the code to display any edits made by user
            for idx, table in enumerate(table_dfs):
                if not table_dfs[idx].equals(st.session_state.table_dfs[idx]):
                    st.session_state.table_dfs = table_dfs
                    st.rerun()

            
            # # Download JSON, will eventually run the submission
            # st.download_button(
            #     label="Download data as JSON",
            #     data=convert_df(table_dfs),
            #     file_name="results.json",
            #     mime="application/json"
            # )
            if 'data_payload' not in st.session_state:
                st.session_state.data_payload = None

            # Generate and display key-value pairs
            if st.button("Generate Key-Value Pairs"):
                # Set first row as header of df
                final_dfs = copy.deepcopy(st.session_state.table_dfs)
                for id, table in enumerate(final_dfs):
                    final_dfs[id] = set_first_row_as_header(table)
                print(final_dfs)
                key_value_pairs = []
                for df in final_dfs:
                    key_value_pairs.extend(ocr_functions.generate_key_value_pairs(df))
                st.write("Completed")
                
                st.session_state.data_payload = json_export(key_value_pairs)
                print(st.session_state.data_payload)
                
            if st.button("Upload to DHIS2"):
                if st.session_state.data_payload is None:
                    raise ValueError("Data empty - generate key value pairs first")
                else:
                    URL = ''
                    ############# write this in OCR functions
                    data_value_set_url = f'{URL}/api/dataValueSets?dryRun=true'
                    # Send the POST request with the data payload
                    response = requests.post(
                        data_value_set_url,
                        auth=('', ''),
                        headers={'Content-Type': 'application/json'},
                        data=st.session_state.data_payload
                    )

                    # # Check the response status
                    # if response.status_code == 200:
                    #     print('Data entry dry run successful')
                    #     print('Response data:')
                    #     print(response.json())
                    # else:
                    #     print(f'Failed to enter data, status code: {response.status_code}')
                    #     print('Response data:')
                    #     print(response.json())
                    st.write("Completed")
