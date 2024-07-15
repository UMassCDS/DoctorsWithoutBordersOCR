import configparser

import requests

# Set these before trying to make requests
DHIS2_USERNAME = None
DHIS2_PASSWORD = None
DHIS2_SERVER_URL = None

# TODO It might be clearer to create a Server object class and have this be the __init__() function
def configure_DHIS2_server(config_path = "settings.ini"):
    config = configparser.ConfigParser()
    config.read(config_path)
    dhis2_section = config["DHIS2Server"]
    global DHIS2_SERVER_URL, DHIS2_USERNAME, DHIS2_PASSWORD
    DHIS2_USERNAME = dhis2_section["username"]
    DHIS2_PASSWORD = dhis2_section["password"]
    DHIS2_SERVER_URL = dhis2_section["server_url"]


# Command to get all fields that are organisationUnits
# TestServerURL/api/organisationUnits.json?fields=:all&includeChildren=true&paging=false
# /api/categoryOptions?fields=name'
# [categories, categoryOptions, dataSets, organisationUnits, dataElements]

# Get all UIDs from list for dataSet, period, orgUnit
# Known Words in dataSet
def getAllUIDs(item_type, search_items):
    filter_param = 'filter=' + '&filter='.join([f'name:ilike:{term}' for term in search_items])

    url = f'{DHIS2_SERVER_URL}/api/{item_type}?{filter_param}'
    response = requests.get(url, auth=(DHIS2_USERNAME, DHIS2_PASSWORD))
    if response.status_code == 401:
        raise ValueError("Authentication failed. Check your username and password.")
    response.raise_for_status()
    
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
    if response.status_code == 401:
        raise ValueError("Authentication failed. Check your username and password.")
    response.raise_for_status()
    
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
        if response.status_code == 401:
            raise ValueError("Authentication failed. Check your username and password.")
        response.raise_for_status()
        
        data = response.json()
        data_set = (data['name'], data['id'], data['periodType'])
        data_sets.append(data_set)
        
    return data_sets