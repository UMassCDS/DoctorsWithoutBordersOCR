import requests

# Command to get all fields that are organisationUnits
# TestServerURL/api/organisationUnits.json?fields=:all&includeChildren=true&paging=false

# Get all UIDs from list for dataSet, period, orgUnit
# Known Words in dataSet
def getAllUIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL):
    filter_param = 'filter=' + '&filter='.join([f'name:ilike:{term}' for term in search_items])

    url = f'{DHIS2_Test_Server_URL}/api/{item_type}?{filter_param}'

    response = requests.get(url, auth=(dhis2_username, dhis2_password))
    response.raise_for_status()
    data = response.json()

    items = data[item_type]
    print(f"{len(data[item_type])} matches found for {search_items}")

    id = [(item['displayName'], item['id']) for item in items]

    return id