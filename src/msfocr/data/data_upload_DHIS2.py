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

    id = [(item['displayName'], item['id']) for item in items]

    return id