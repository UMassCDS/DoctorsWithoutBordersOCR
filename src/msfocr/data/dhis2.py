import urllib.parse

import requests

# Make sure these are set before trying to make requests
DHIS2_USERNAME = None
DHIS2_PASSWORD = None
DHIS2_SERVER_URL = None

# TODO It might be clearer to create a Server object class and have this be the __init__() function
def configure_DHIS2_server(username=None, password=None, server_url=None):
    global DHIS2_SERVER_URL, DHIS2_USERNAME, DHIS2_PASSWORD
    DHIS2_USERNAME = username
    DHIS2_PASSWORD = password
    DHIS2_SERVER_URL = server_url

def getAllUIDs(item_type, search_items):
    encoded_search_items = [urllib.parse.quote_plus(item) for item in search_items]

    if item_type=='dataElements':
        filter_param = 'filter=' + '&filter='.join([f'formName:ilike:{term}' for term in encoded_search_items])
    else:
        filter_param = 'filter=' + '&filter='.join([f'name:ilike:{term}' for term in encoded_search_items])
        
    url = f'{DHIS2_SERVER_URL}/api/{item_type}?{filter_param}'
    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    checkResponseStatus(response)

    data = response.json()
    items = data[item_type]
    print(f"{len(data[item_type])} matches found for {search_items}")
    if len(items) > 0:
        print(items[0])

    uid = [(item['displayName'], item['id']) for item in items]

    return uid

def checkResponseStatus(res):
    if res.status_code == 401:
        raise ValueError("Authentication failed. Check your username and password.")
    res.raise_for_status()

def getOrgUnitChildren(uid):
    """
    Searches DHIS2 for all the direct children of an organization unit.
    :param uid: String of organization unit UID
    :return: List of (org unit child name, org unit child data sets))
    """
    url = f'{DHIS2_SERVER_URL}/api/organisationUnits/{uid}?includeChildren=true'
    
    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    checkResponseStatus(response)
    
    data = response.json()
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
        
        response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
        checkResponseStatus(response)
        
        data = response.json()
        data_set = (data['name'], data['id'], data['periodType'])
        data_sets.append(data_set)
        
    return data_sets

def getFormJson(dataSet_uid, period, orgUnit_uid):
    url = f'{DHIS2_SERVER_URL}/api/dataSets/{dataSet_uid}/form.json?pe={period}&ou={orgUnit_uid}'

    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    checkResponseStatus(response)
    
    data = response.json()
    return data
            
def get_DE_COC_List(form, allDataElements, allCategory):
    # Form tabs found in DHIS2
    tabs = form['groups']
    dataElement_list = {}
    categoryOptionCombo_list = {}
    for tab in tabs:
        for field in tab['fields']:
            DE_ID = tab['dataElement']
            COC_ID = tab['categoryOptionCombo']
            if allDataElements[DE_ID] not in dataElement_list:
                dataElement_list[allDataElements[DE_ID]] = 1
            if allCategory[COC_ID] not in categoryOptionCombo_list:
                categoryOptionCombo_list[allCategory[COC_ID]] = 1
    return list(dataElement_list.keys()), list(categoryOptionCombo_list.keys())   


