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


def checkResponseStatus(res):
    if res.status_code == 401:
        raise ValueError("Authentication failed. Check your username and password.")
    res.raise_for_status()


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

def getCategoryUIDs(dataSet_uid):
    """
    Hierarchically searches DHIS2 to generate category UIDs for each dataElement. Also used for retreiving all data elements and categories present in a dataset.
    :param data_sets_uid: UID of the dataset
    :return: dataElement_to_id (dict[str, str]), dataElement_to_categoryCombo (dict[str, str]), categoryCombos (dict[str, str]), category_list (list[str]), dataElement_list (list[str])
             category list eg. ['0-11m','<5y'...]
    """
    url = f'{DHIS2_SERVER_URL}/api/dataSets/{dataSet_uid}?fields=dataSetElements'

    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    checkResponseStatus(response)
    
    data = response.json()

    items = data['dataSetElements']

    dataElement_to_categoryCombo = {}
    categoryCombos = {}
    categoryOptionCombos = {}
    for item in items:
        if 'categoryCombo' in item:
            dataElement_to_categoryCombo[item['dataElement']['id']] = item['categoryCombo']['id']
            categoryCombos[item['categoryCombo']['id']] = {}
 
    for catCombo_id in categoryCombos:
        url = f'{DHIS2_SERVER_URL}/api/categoryCombos/{catCombo_id}?fields=categoryOptionCombos'

        response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
        checkResponseStatus(response)
        
        data = response.json()

        items = data['categoryOptionCombos']

        for item in items:
            url = f"{DHIS2_SERVER_URL}/api/categoryOptionCombos/{item['id']}?fields=name"

            response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
            checkResponseStatus(response)
            
            data = response.json()

            categoryCombos[catCombo_id][data['name']] = item['id']

            if data['name'] not in categoryOptionCombos:
                categoryOptionCombos[data['name']] = ''
    category_list = list(categoryOptionCombos.keys())
                                    
    url = f'{DHIS2_SERVER_URL}/api/dataElements?filter=dataSetElements.dataSet.id:eq:{dataSet_uid}&fields=id,formName'
    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    checkResponseStatus(response)
    data = response.json()                   

    dataElement_to_id = {item["formName"]:item["id"] for item in data['dataElements']}
    dataElement_list = [item["formName"] for item in data['dataElements']]

    return dataElement_to_id, dataElement_to_categoryCombo, categoryCombos, category_list, dataElement_list       
       

