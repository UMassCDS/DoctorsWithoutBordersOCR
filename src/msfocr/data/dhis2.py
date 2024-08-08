import urllib.parse
import json
import requests

# Make sure these are set before trying to make requests
DHIS2_USERNAME = None
DHIS2_PASSWORD = None
DHIS2_SERVER_URL = None

# TODO It might be clearer to create a Server object class and have this be the __init__() function
def configure_DHIS2_server(username=None, password=None, server_url=None):
    global DHIS2_SERVER_URL, DHIS2_USERNAME, DHIS2_PASSWORD
    if username is not None: 
        DHIS2_USERNAME = username
    if password is not None: 
        DHIS2_PASSWORD = password
    if server_url is not None: 
        DHIS2_SERVER_URL = server_url

def getAllUIDs(item_type, search_items):
    encoded_search_items = [urllib.parse.quote_plus(item) for item in search_items]

    if item_type=='dataElements':
        filter_param = 'filter=' + '&filter='.join([f'formName:ilike:{term}' for term in encoded_search_items])
    else:
        filter_param = 'filter=' + '&filter='.join([f'name:ilike:{term}' for term in encoded_search_items])
        
    url = f'{DHIS2_SERVER_URL}/api/{item_type}?{filter_param}'
    data = getResponse(url)
    items = data[item_type]
    print(f"{len(data[item_type])} matches found for {search_items}")
    if len(items) > 0:
        print(items[0])

    uid = [(item['displayName'], item['id']) for item in items]

    return uid

def getResponse(url):
    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))

    if response.status_code == 401:
        raise ValueError("Authentication failed. Check your username and password.")
    response.raise_for_status()

    data = response.json()
    return data

def getOrgUnitChildren(uid):
    """
    Searches DHIS2 for all the direct children of an organization unit.
    :param uid: String of organization unit UID
    :return: List of (org unit child name, org unit child data sets))
    """
    url = f'{DHIS2_SERVER_URL}/api/organisationUnits/{uid}?includeChildren=true'
    data = getResponse(url)
    items = data['organisationUnits']
    children = [(item['name'], item['dataSets'], item['id']) for item in items if item['id'] != uid]
    
    return children

def getDataSets(data_sets_uids):
    """
    Searches DHIS2 for every data set given in a list.
    :param data_sets_uids: List of data set objects retrieved from DHIS2
    :return: List of (data set name, data set id))
    """
    data_sets = []
    
    for uid_obj in data_sets_uids:
        uid = uid_obj['id']
        url = f'{DHIS2_SERVER_URL}/api/dataSets/{uid}'
        
        data = getResponse(url)
        data_set = (data['name'], data['id'], data['periodType'])
        data_sets.append(data_set)
        
    return data_sets

def getFormJson(dataSet_uid, period, orgUnit_uid):
    """
    Gets information about all forms associated with a organisation, dataset, period combination in DHIS2.
    :param dataset UID, time period, organisation unit UID
    :return json response containing hierarchical information about tabs, tables, non-tabular fields
    """
    
    # POST empty data payload to trigger form generation
    json_export = {}
    json_export["dataSet"] = dataSet_uid
    json_export["period"] = period
    json_export["orgUnit"] = orgUnit_uid
    json_export["dataValues"] = []
    data_payload = json.dumps(json_export)
    posturl = f'{DHIS2_SERVER_URL}/api/dataValueSets?dryRun=true' 

    response = requests.post(
                        posturl,
                        auth=(DHIS2_USERNAME, DHIS2_PASSWORD),
                        headers={'Content-Type': 'application/json'},
                        data=data_payload
                    )  
    response.raise_for_status()

    # Get form now
    url = f'{DHIS2_SERVER_URL}/api/dataSets/{dataSet_uid}/form.json?pe={period}&ou={orgUnit_uid}'
    data = getResponse(url)
    return data
            
def get_DE_COC_List(form):
    """
    Finds the list of all dataElements (row names in tables) and categoryOptionCombos (column names in tables) within a DHIS2 form
    :param json data containing hierarchical information about tabs, tables, non-tabular fields within a organisation, dataset, period combination in DHIS2. 
    :return List of row names found, List of column names found 
    """
    url = f'{DHIS2_SERVER_URL}/api/dataElements?paging=false&fields=id,formName'
    data = getResponse(url)
    allDataElements = {item['id']:item['formName'] for item in data['dataElements'] if 'formName' in item and 'id' in item}

    url = f'{DHIS2_SERVER_URL}/api/categoryOptionCombos?paging=false&fields=id,name'
    data = getResponse(url)
    allCategory = {item['id']:item['name'] for item in data['categoryOptionCombos'] if 'name' in item and 'id' in item}

    # Form tabs found in DHIS2
    tabs = form['groups']
    dataElement_list = {}
    categoryOptionCombo_list = {}
    for tab in tabs:
        for field in tab['fields']:
            DE_ID = field['dataElement']
            COC_ID = field['categoryOptionCombo']
            if allDataElements[DE_ID] not in dataElement_list:
                dataElement_list[allDataElements[DE_ID]] = 1
            if allCategory[COC_ID] not in categoryOptionCombo_list:
                categoryOptionCombo_list[allCategory[COC_ID]] = 1
    return list(dataElement_list.keys()), list(categoryOptionCombo_list.keys())   


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
