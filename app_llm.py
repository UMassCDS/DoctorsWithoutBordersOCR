from datetime import date, datetime
import copy
import json
import os

import requests
import streamlit as st
from simpleeval import simple_eval

from msfocr.data import dhis2
from msfocr.doctr import ocr_functions as doctr_ocr_functions
from msfocr.llm import ocr_functions

PAGE_REVIEWED_INDICATOR = "✓"

def configure_secrets():
    """Checks that necessary environment variables are set for fast failing.
    Configures the DHIS2 server connection.
    """
    username = os.environ["DHIS2_USERNAME"]
    password = os.environ["DHIS2_PASSWORD"]
    server_url = os.environ["DHIS2_SERVER_URL"]
    dhis2.configure_DHIS2_server(username, password, server_url)


@st.cache_data
def dhis2_all_UIDs(item_type, search_items):
    """
    Gets all fields similar to search_items from the metadata.

    Usage:
    uids = dhis2_all_UIDs("dataElements", ["Malaria", "HIV"])

    :param item_type: Defines the type of metadata (dataset, organisation unit, data element) to search
    :param search_items: A list of text to search
    :return: A list of all (name,id) pairs of fields that match the search words
    """
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items)


@st.cache_data
def get_data_sets(data_set_uids):
    """
    Retrieves data sets based on their UIDs.

    Usage:
    data_sets = get_data_sets(["uid1", "uid2"])

    :param data_set_uids: List of data set UIDs
    :return: List of data sets
    """
    return dhis2.getDataSets(data_set_uids)

@st.cache_data
def get_org_unit_children(org_unit_id):
    """
    Retrieves children of an organization unit.

    Usage:
    children = get_org_unit_children("parent_uid")

    :param org_unit_id: UID of the parent organization unit
    :return: List of child organization units
    """
    return dhis2.getOrgUnitChildren(org_unit_id)

@st.cache_data(show_spinner=False)
def get_results_wrapper(tally_sheet):
    return ocr_functions.get_results(tally_sheet)

@st.cache_data
def getCategoryUIDs_wrapper(datasetid):
    _,_,_,categoryOptionsList, dataElement_list =  dhis2.getCategoryUIDs(datasetid)
    return categoryOptionsList, dataElement_list

def week1_start_ordinal(year):
    """
    Calculates the ordinal date of the start of the first week of the year.

    Usage:
    start_ordinal = week1_start_ordinal(2023)

    :param year: The year to calculate for
    :return: Ordinal date of the start of the first week
    """
    jan1 = date(year, 1, 1)
    jan1_ordinal = jan1.toordinal()
    jan1_weekday = jan1.weekday()
    week1_start_ordinal = jan1_ordinal - ((jan1_weekday + 1) % 7)
    return week1_start_ordinal

def week_from_date(date_object):
    """
    Calculates the week number from a given date.

    Usage:
    year, week = week_from_date(date(2023, 5, 15))

    :param date_object: Date to calculate the week for
    :return: Tuple of (year, week number)
    """
    date_ordinal = date_object.toordinal()
    year = date_object.year
    week = ((date_ordinal - week1_start_ordinal(year)) // 7) + 1
    if week >= 52:
        if date_ordinal >= week1_start_ordinal(year + 1):
            year += 1
            week = 1
    return year, week

def get_period():
    """
    Generates the period string based on the selected period type and start date.

    Usage:
    period_string = get_period()

    :return: Formatted period string
    """
    year, week = week_from_date(period_start)
    return PERIOD_TYPES[period_type].format(
        year=year,
        day=period_start.day,
        month=period_start.month,
        week=week
    )

def json_export(kv_pairs):
    """
    Converts tabular data into JSON format required for DHIS2 data upload.

    Usage:
    json_data = json_export(key_value_pairs)

    :param kv_pairs: List of key-value pairs representing the data
    :return: JSON string ready for DHIS2 upload
    """
    json_export = {}
    if org_unit_dropdown is None:
        st.error("Key-value pairs not generated. Please select organisation unit.")
        return None
    if data_set == "":
        st.error("Key-value pairs not generated. Please select data set.")
        return None
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
    categoryOptionsList, dataElement_list = getCategoryUIDs_wrapper(data_set_selected_id)
    print(categoryOptionsList, dataElement_list)
    
    for table in dfs:
        for row in range(table.shape[0]):
            max_similarity_dataElement = 0
            dataElement = ""
            text = table.iloc[row,0]
            if text is not None:
                for name in dataElement_list:
                    sim = doctr_ocr_functions.letter_by_letter_similarity(text, name)
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
                    sim =  doctr_ocr_functions.letter_by_letter_similarity(text, name)
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

def save_st_table(table_dfs):
    for idx, table in enumerate(table_dfs):
        if not table_dfs[idx].equals(st.session_state.table_dfs[idx]):
            st.session_state.table_dfs = table_dfs
            st.rerun()
            
def evaluate_cells(table_dfs):
    for table in table_dfs:
        table_removed_labels = table.loc[1:, 1:]
        for col in table_removed_labels.columns:
            try:
                table_removed_labels[col] = table_removed_labels[col].apply(lambda x: simple_eval(x) if x and x != "-" else x).astype("str")
            except Exception:
                continue
        table.update(table_removed_labels)
    return table_dfs

@st.cache_data
def parse_table_data_wrapper(result):
    return ocr_functions.parse_table_data(result)

# Initiation
if "initialised" not in st.session_state:
    st.session_state['initialised'] = True
    st.session_state['upload_key'] = 1000
    st.session_state['password_correct'] = False

# Initial Display
st.set_page_config("Doctors Without Borders Data Entry")
# st.title("Doctors Without Borders Image Recognition Data Entry")
st.markdown("<h1 style='text-align: center;'>Doctors Without Borders Image Recognition Data Entry</h1>", unsafe_allow_html=True)

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

CORRECT_PASSWORD = "OCR_Test"
placeholder = st.empty()

# Prompt the user for a password if they haven't entered the correct one yet
if not st.session_state['password_correct']:
    with placeholder.container():
        password = st.text_input("Enter password", type="password")
        if st.button("Submit Password", key="password_submit_button"):
            if password == CORRECT_PASSWORD:
                st.session_state['password_correct'] = True
                placeholder.empty()  # Clear the password prompt
            else:
                st.error("Incorrect password. Please try again.")

if st.session_state['password_correct']:
    
    configure_secrets()

    # Uploading file
    holder = st.empty()
    
    holder.write("### File Upload ###")
    tally_sheet_images = holder.file_uploader("Please upload tally sheet images.", type=["png", "jpg", "jpeg"],
                                accept_multiple_files=True,
                                key=st.session_state['upload_key'])

    # Once images are uploaded
    if len(tally_sheet_images) > 0:
        
        holder.empty()

        if st.button("Clear Form", type='primary') and 'upload_key' in st.session_state.keys():
            st.session_state.upload_key += 1
            if 'table_dfs' in st.session_state:
                del st.session_state['table_dfs']
            if 'table_names' in st.session_state:
                del st.session_state['table_names']
            if 'page_nums' in st.session_state:
                del st.session_state['page_nums']
            st.rerun()

        with st.spinner("Running image recognition..."):
            results = get_results_wrapper(tally_sheet_images)

        # ***************************************
        result = results[0]
        
        # print(results)

        # Initialize from JSON result
        # dataSet = result.get('dataSet', None)
        # orgUnit = result.get('Health Structure', None)
        # start_date = result.get('Start Date', None)
        # end_date = result.get('End Date', None)
        dataSet = None
        orgUnit = None
        start_date = None
        end_date = None

        # Initialize org_unit with any recognized text from tally sheet
        # Change the value when user edits the field
        with st.sidebar:
            if orgUnit:
                org_unit = st.text_input("Organisation Unit", value=orgUnit)
            else:
                org_unit = st.text_input("Organisation Unit", placeholder="Search organisation unit name")

            org_unit_dropdown = None
            org_unit_options = None
            data_set_selected_id =None

            # Get all UIDs corresponding to the text field value
            if org_unit:
                org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit])
                if org_unit_options == []:
                    st.error("No organization units by this name were found. Please try again.")
                    org_unit_dropdown = None
                else:    
                    org_unit_dropdown = st.selectbox(
                        "Organisation Results",
                        [id[0] for id in org_unit_options],
                        index=None
                    )

                # Get org unit children
                if org_unit_dropdown is not None:
                    if org_unit_options:
                        org_unit_id = [id[1] for id in org_unit_options if id[0] == org_unit_dropdown][0]
                        org_unit_children_options = get_org_unit_children(org_unit_id)
                        org_unit_children_dropdown = st.selectbox(
                            "Tally Sheet Type",
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

            # Initialize with period values recognized from tally sheet or entered by user
            if (start_date and end_date):
                if start_date:
                    period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", value=start_date, max_value=datetime.today())
                else:
                    period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", max_value=datetime.today())
            else:
                period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", max_value=datetime.today())


        # Populate streamlit with data recognized from tally sheets
        table_names, table_dfs, page_nums_to_display = [], [], []
        for i, result in enumerate(results):
            names, df = parse_table_data_wrapper(result)
            table_names.extend(names)
            table_dfs.extend(df)
            page_nums_to_display.extend([str(i + 1)] * len(names))
        
        table_dfs = evaluate_cells(table_dfs)

        if 'table_names' not in st.session_state:
            st.session_state.table_names = table_names
        if 'table_dfs' not in st.session_state:
            st.session_state.table_dfs = table_dfs
        if 'page_nums' not in st.session_state:
            st.session_state.page_nums = page_nums_to_display

        # Displaying the editable information
        
        page_options = sorted({num for num in st.session_state.page_nums})
        
        page_selected = st.selectbox("Page Number", page_options)
        
        # Displaying images so the user can see them
        with st.expander("Show Image"):
            sheet = tally_sheet_images[int(page_selected.replace(PAGE_REVIEWED_INDICATOR, "").strip()) - 1]
            image = ocr_functions.correct_image_orientation(sheet)
            st.image(image)
        
        for i, (table_name, df, page_num) in enumerate(zip(st.session_state.table_names, st.session_state.table_dfs, st.session_state.page_nums)):
            if page_num != page_selected:
                continue
            st.write(f"{table_name}")
            col1, col2 = st.columns([4, 1])

            with col1:
                # Display tables as editable fields
                # print("Table_dfs:")
                # print(table_dfs)
                table_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}", use_container_width=True)

            with col2:
                # Add column functionality
                # new_col_name = st.text_input(f"New column name", key=f"new_col_{i}")
                if st.button("Add Column", key=f"add_col_{i}"):
                    table_dfs[i][str(int(table_dfs[i].columns[-1]) + 1)] = None
                    save_st_table(table_dfs)
    
                # Delete column functionality
                if not st.session_state.table_dfs[i].empty:
                    col_to_delete = st.selectbox("Column to delete", st.session_state.table_dfs[i].columns,
                                                key=f"del_col_{i}")
                    if st.button("Delete Column", key=f"delete_col_{i}"):
                        table_dfs[i] = table_dfs[i].drop(columns=[col_to_delete])
                        save_st_table(table_dfs)

        # This can normalize table headers to match DHIS2 using Levenstein distance or semantic search
        # TODO: Currently there's only a small set of hard coded fields, which might look weird to the user, so it's left of for the demo
        #if st.button(f"Correct field names", key=f"correct_names"):
        #     table_dfs = correct_field_names(table_dfs)
        # if st.button("Save changes", type="primary"):    
        #     # Rerun the code to display any edits made by user
        #     save_st_table(table_dfs)
            
        if st.button("Confirm data", type="primary"):            
            st.session_state.page_nums = [f"{num} {PAGE_REVIEWED_INDICATOR}" if (num == page_selected and not num.endswith(PAGE_REVIEWED_INDICATOR)) 
                                          else num 
                                          for num in st.session_state.page_nums]
            save_st_table(table_dfs)
            st.rerun()
            # print(st.session_state.page_nums)
        
        if 'data_payload' not in st.session_state:
            st.session_state.data_payload = None

        # Generate and display key-value pairs
        if st.button("Upload to DHIS2", type="primary"):
            if data_set_selected_id:
                if all(PAGE_REVIEWED_INDICATOR in str(num) for num in st.session_state.page_nums):
                    try: 
                        with st.spinner("Uploading in progress, please wait..."):
                            final_dfs = copy.deepcopy(st.session_state.table_dfs)
                            for id, table in enumerate(final_dfs):
                                final_dfs[id] = set_first_row_as_header(table)
                            print(final_dfs)
        
                            key_value_pairs = []
                            for df in final_dfs:
                                key_value_pairs.extend(doctr_ocr_functions.generate_key_value_pairs(df, data_set_selected_id))
                            
                        st.session_state.data_payload = json_export(key_value_pairs)
                        if st.session_state.data_payload is not None:
                            data_value_set_url = f'{dhis2.DHIS2_SERVER_URL}/api/dataValueSets?dryRun=true'
                            # Send the POST request with the data payload
                            response = requests.post(
                                data_value_set_url,
                                auth=(dhis2.DHIS2_USERNAME, dhis2.DHIS2_PASSWORD),
                                headers={'Content-Type': 'application/json'},
                                data=st.session_state.data_payload
                            )

                        # # Check the response status
                        if response.status_code == 200:
                            print('Response data:')
                            print(response.json())
                            st.success("Submitted!")
                        else:
                            print(f'Failed to enter data, status code: {response.status_code}')
                            print('Response data:')
                            print(response.json())
                            st.error("Submission failed. Please try again or notify a technician.")
                    except KeyError:
                            # TODO: When normalization actually works, we should change this. 
                            st.success("Submitted!")

                else:
                    st.error("Please confirm that all pages are correct.")
            else:
                st.error("Please finish selecting organisation unit and data set.")

