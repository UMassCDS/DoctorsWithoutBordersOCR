from datetime import date, datetime
import copy
import json
import os
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth
from simpleeval import simple_eval
from msfocr.data import dhis2
from msfocr.doctr import ocr_functions as doctr_ocr_functions
from msfocr.llm import ocr_functions


# Hardcoded period types and formatting, probably won't update but can get them through API
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

PAGE_REVIEWED_INDICATOR = "✓"

# Wrapper functions
@st.cache_data(show_spinner=False)
def get_results_wrapper(tally_sheet):
    """A wrapper function for caching the get_results function."""
    return ocr_functions.get_results(tally_sheet)


@st.cache_data
def get_DE_COC_List_wrapper(form):
    """A wrapper function for caching the get_DE_COC_List function."""
    dataElement_list, categoryOptionsList =  dhis2.get_DE_COC_List(form)
    return dataElement_list, categoryOptionsList


@st.cache_data
def getFormJson_wrapper(data_set_selected_id, period_ID, org_unit_dropdown):
    """A wrapper function for caching the getFormJson function."""
    return dhis2.getFormJson(data_set_selected_id, period_ID, org_unit_dropdown)


@st.cache_data
def parse_table_data_wrapper(result):
    """A wrapper function for caching the parse_table_data_wrapper function."""
    tablenames, tables =  ocr_functions.parse_table_data(result)
    return tablenames, tables


@st.cache_data
def get_data_sets(data_set_uids):
    """
    Retrieves data sets based on their UIDs. Wrapper function.

    Usage:
    data_sets = get_data_sets(["uid1", "uid2"])

    :param data_set_uids: List of data set UIDs
    :return: List of data sets
    """
    return dhis2.getDataSets(data_set_uids)


@st.cache_data
def get_org_unit_children(org_unit_id):
    """
    Retrieves children of an organization unit. Wrapper function.

    Usage:
    children = get_org_unit_children("parent_uid")

    :param org_unit_id: UID of the parent organization unit
    :return: List of child organization units
    """
    return dhis2.getOrgUnitChildren(org_unit_id)


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


def correct_field_names(dfs, form):
    """
    Corrects the text data in tables by replacing with closest match among the hardcoded fieldnames.
    
    :param dfs: Data as dataframes
    :return: Corrected data as dataframes
    """
    dataElement_list,categoryOptionsList = get_DE_COC_List_wrapper(form)
    
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


def set_first_row_as_header(df):
    """
    Sets the first row in the recognized table (ideally the header information for each column) as the table header
    :param Dataframe
    :return Dataframe after correction
    """
    df.columns = df.iloc[0]  
    df = df.iloc[1:]  
    df.reset_index(drop=True, inplace=True)
    return df


def save_st_table(table_dfs):
    """Saves the tables to the session state if there are any changes and reruns."""
    for idx, table in enumerate(table_dfs):
        if not table_dfs[idx].equals(st.session_state.table_dfs[idx]):
            st.session_state.table_dfs = table_dfs
            st.rerun()
            
            
def evaluate_cells(table_dfs):
    """Uses simple_eval to perform math operations on each cell, defaulting to input if failed.

    Args:
        table_dfs (_List_): List of table data frames

    Returns:
        _List_: List of table data frames
    """
    for table in table_dfs:
        table_removed_labels = table.loc[1:, 1:]
        for col in table_removed_labels.columns:
            try:
                # Contents should be strings in order to be editable later
                table_removed_labels[col] = table_removed_labels[col].apply(lambda x: simple_eval(x) if x and x != "-" else x).astype("str")
            except Exception:
                continue
        table.update(table_removed_labels)
    return table_dfs


# Initializing session state variables that only need to be set on startup
if "initialised" not in st.session_state:
    st.session_state['initialised'] = True
    st.session_state['upload_key'] = 1000
    st.session_state['password_correct'] = False
    

# *****Page display*****

# Title and browser tab naming
st.set_page_config("Doctors Without Borders Data Entry")
st.markdown("<h1 style='text-align: center;'>Doctors Without Borders Image Recognition Data Entry</h1>", unsafe_allow_html=True)

server_url = os.environ["DHIS2_SERVER_URL"]
dhis2.configure_DHIS2_server(server_url = server_url)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'password' not in st.session_state:
    st.session_state['password'] = ""
if 'auth_failed' not in st.session_state:
    st.session_state['auth_failed'] = False

placeholder = st.empty()

def authenticate():
    response = requests.get(f'{dhis2.DHIS2_SERVER_URL}/api/33/me', auth=HTTPBasicAuth(st.session_state['username'], st.session_state['password']))
    if response.status_code == 200:
        st.session_state['authenticated'] = True
        st.session_state['auth_failed'] = False
        st.session_state['user_info'] = response.json()
    else:
        st.session_state['auth_failed'] = True

# Prompt the user for username and password if they haven't entered them yet
if not st.session_state['authenticated']:
    with placeholder.container():
        st.session_state['username'] = st.text_input("Enter DHIS2 username")
        st.session_state['password'] = st.text_input("Enter DHIS2 password", type="password")
        if st.button("Submit", key="auth_submit_button"):
            authenticate()

# Display an error message if authentication failed
if st.session_state['auth_failed']:
    st.error("Incorrect username or password. Please try again.")

if st.session_state['authenticated']:
    placeholder.empty()
    
    dhis2.configure_DHIS2_server(username = st.session_state['username'], password=st.session_state['password'])

    api_key = os.environ["AZURE_OPENAI_API_KEY"]
    azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    ocr_functions.configure_azure_openai(api_key = api_key, azure_endpoint=azure_endpoint)

    # File upload layout
    upload_holder = st.empty()
    
    upload_holder.write("### File Upload ###")
    tally_sheet_images = upload_holder.file_uploader("Please upload tally sheet images.", type=["png", "jpg", "jpeg"],
                                accept_multiple_files=True,
                                key=st.session_state['upload_key'])

    # Once images are uploaded
    if len(tally_sheet_images) > 0:
        
        # Removing the data upload file button to force users to clear form
        upload_holder.empty()

        # Clearing form removes form-related session states
        if st.button("Clear Form", type='primary') and 'upload_key' in st.session_state.keys():
            st.session_state.upload_key += 1
            if 'table_dfs' in st.session_state:
                del st.session_state['table_dfs']
            if 'table_names' in st.session_state:
                del st.session_state['table_names']
            if 'page_nums' in st.session_state:
                del st.session_state['page_nums']
            if 'pages_confirmed' in st.session_state:
                del st.session_state['pages_confirmed']
            st.rerun()

        # Sidebar for header data
        with st.sidebar:
            org_unit = st.text_input("Organisation Unit", placeholder="Search organisation unit name")

            # Initializing variables that will be called later on
            org_unit_dropdown = None
            org_unit_options = None
            org_unit_child_id = None
            data_set_selected_id = None
            period_type=None
            
            # Successive if-statements: simulate tree layout, needs prior values
            if org_unit:
                # Get all UIDs corresponding to the text field value
                org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit])
                
                if org_unit_options == []:
                    st.error("No organization units by this name were found. Please try again.")
                    
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

                        # Get data sets
                        if org_unit_children_dropdown is not None:

                            org_unit_child_id = [id[2] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
                            data_set_ids = [id[1] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
                            data_set_options = get_data_sets(data_set_ids)
                            data_set = st.selectbox(
                                "Data Set",
                                sorted([id[0] for id in data_set_options]),
                                index=None
                            )

                            # Display period types
                            if data_set is not None:
                                data_set_selected_id = [id[1] for id in data_set_options if id[0] == data_set][0]
                                period_type = [id[2] for id in data_set_options if id[0] == data_set][0]
                                st.write("Period Type\: " + period_type)

            # Initialize with today's date, then entered by user
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", max_value=datetime.today())
            # End sidebar


        # Spinner for data upload. If it's going to be on screen for long, make it bespoke 
        with st.spinner("Running image recognition..."):
            results = get_results_wrapper(tally_sheet_images)

        # ***************************************
        
        # Populate streamlit with data recognized from tally sheets
        
        table_names, table_dfs, page_nums_to_display = [], [], []
        for i, result in enumerate(results):
            names, df = parse_table_data_wrapper(result)
            table_names.extend(names)
            table_dfs.extend(df)
            page_nums_to_display.extend([str(i + 1)] * len(names))
        table_dfs = evaluate_cells(table_dfs)
        
        # Form session state initialization
        if 'table_names' not in st.session_state:
            st.session_state.table_names = table_names
        if 'table_dfs' not in st.session_state:
            st.session_state.table_dfs = table_dfs
        if 'page_nums' not in st.session_state:
            st.session_state.page_nums = page_nums_to_display
        if 'data_payload' not in st.session_state:
            st.session_state.data_payload = None
        if 'pages_confirmed' not in st.session_state:
            st.session_state['pages_confirmed'] = False

        # Displaying the editable information
        # Used for multipage selection functionality
        page_options = sorted({num for num in st.session_state.page_nums}, key=lambda k: int(k.replace(PAGE_REVIEWED_INDICATOR, "")))
        current_page = next((i for i, num in enumerate(page_options) if not num.endswith(PAGE_REVIEWED_INDICATOR)), 0)
        page_selected = st.selectbox("Page Number", page_options, index=int(current_page))
        
        # Displaying images so the user can see them
        with st.expander("Show Image"):
            sheet = tally_sheet_images[int(page_selected.replace(PAGE_REVIEWED_INDICATOR, "").strip()) - 1]
            image = ocr_functions.correct_image_orientation(sheet)
            st.image(image)
        
        # Uploading the tables, adding columns for each name
        for i, (table_name, df, page_num) in enumerate(zip(st.session_state.table_names, st.session_state.table_dfs, st.session_state.page_nums)):
            if page_num != page_selected:
                continue
            st.write(f"{table_name}")
            col1, col2 = st.columns([4, 1])

            with col1:
                # Display tables as editable fields
                table_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}", use_container_width=True)

            with col2:
                # Add column functionality
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

        # Following button functionality relies on the data set to be selected, hence the blocker
        if data_set_selected_id:
    
            period_ID = get_period()
            # Get the information about the DHIS2 form after all form identifiers have been selected by the user    
            form = getFormJson_wrapper(data_set_selected_id, period_ID, org_unit_child_id)

            # Correct field names button
            if st.button("Correct to DHIS2 field names", key="correct_names", type="primary"):
            # This can normalize table headers to match DHIS2 using Levenstein distance or semantic search    
                if data_set_selected_id:
                    edited_dfs = correct_field_names(table_dfs, form)
                    save_st_table(edited_dfs)
                else:
                    raise Exception("Select a valid dataset") 
                
                
            # Confirm data button
            if st.button("Confirm data", type="primary"):            
                st.session_state.page_nums = [f"{num} {PAGE_REVIEWED_INDICATOR}" if (num == page_selected and not num.endswith(PAGE_REVIEWED_INDICATOR)) 
                                            else num 
                                            for num in st.session_state.page_nums]
                st.session_state.pages_confirmed = all(ele.endswith(PAGE_REVIEWED_INDICATOR) for ele in st.session_state.page_nums)
                # In case the user didn't change anything and confirmed, it will reload and move to the next one regardless.
                save_st_table(table_dfs)
                st.rerun()
                
    
            # Generate and display key-value pairs button
            if st.button("Generate key value pairs", type="primary", disabled=not st.session_state.pages_confirmed):
                try:
                    # Bespoke spinner 2
                    with st.spinner("Key value pair generation in progress, please wait..."):
                        # Copying the session state dfs so that any non-confirmed changes aren't used
                        final_dfs = copy.deepcopy(st.session_state.table_dfs)
                        for id, table in enumerate(final_dfs):
                            final_dfs[id] = set_first_row_as_header(table)

                        key_value_pairs = []
                        for df in final_dfs:
                            key_value_pairs.extend(doctr_ocr_functions.generate_key_value_pairs(df, form))
                        
                        st.session_state.data_payload = json_export(key_value_pairs)

                        # Displaying the data payload as requested
                        st.write("### Data payload ###")
                        st.json(st.session_state.data_payload)
                except KeyError as e:
                    raise Exception("Key error - ", e)


            # Upload to DHIS2 button
            if st.button("Upload to DHIS2", type="primary", disabled=not st.session_state.pages_confirmed):
                # Check that every page has been confirmed
                if all(PAGE_REVIEWED_INDICATOR in str(num) for num in st.session_state.page_nums):
                    if st.session_state.data_payload is not None:
                        data_value_set_url = f'{dhis2.DHIS2_SERVER_URL}/api/dataValueSets?dryRun=true'
                        # Send the POST request with the data payload
                        response = requests.post(
                            data_value_set_url,
                            auth=(dhis2.DHIS2_USERNAME, dhis2.DHIS2_PASSWORD),
                            headers={'Content-Type': 'application/json'},
                            data=st.session_state.data_payload
                        )
                    else:
                        st.error("Generate key value pairs first")
                    # Check the response status
                    if response.status_code == 200:
                        st.success("Submitted!")
                    else:
                        st.error("Submission failed. Please try again or notify a technician.")
                else: 
                    st.error("Please confirm that all pages are correct.")

        # Corresponding to the if statement for button check
        else:
            st.error("Please finish selecting organisation unit and data set.")