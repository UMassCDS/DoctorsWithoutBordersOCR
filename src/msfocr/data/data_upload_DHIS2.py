import requests

dhis2_username = ''
dhis2_password = ''
DHIS2_Test_Server_URL = 'https://ocr.twoca.org/'


# Command to get all fields that are organisationUnits
# TestServerURL/api/organisationUnits.json?fields=:all&includeChildren=true&paging=false
# /api/categoryOptions?fields=name'
# [categories, categoryOptions, dataSets, organisationUnits, dataElements]

# Get UIDS for dataSet, period, orgUnit
def getUID(item_type, search_items):
    filter_param = 'filter=' + '&filter='.join([f'name:ilike:{term}' for term in search_items])

    url = f'{DHIS2_Test_Server_URL}/api/{item_type}?{filter_param}'

    if dhis2_username == '' or dhis2_password == '':
        print("Enter username and password")

    response = requests.get(url, auth=(dhis2_username, dhis2_password))
    data = response.json()

    items = data[item_type]
    print(f"{len(data[item_type])} matches found for {search_items}")
    print(items)

    id = items[0]['id']

    return id


# # dataSets, organisationUnits, period, categoryCombos
# search_items_dataSet = ['Kutupalong', 'Sunday', 'Balukhali']
# search_items_orgUnit = ['General OPD']
# search_items_categoryCombo = ['<5y', 'Resident']
# search_items_dataElements = ['Available consultation days']

# item_type = 'dataSets'
# dataSet_id = getUID(item_type, search_items_dataSet)
# item_type = 'organisationUnits'
# orgUnit_id = getUID(item_type, search_items_orgUnit)
# item_type = 'dataElements'
# dataElement_id = getUID(item_type, search_items_dataElements)
# # item_type = 'categoryOptions'
# # categoryCombos_id = getUID(item_type, search_items_categoryCombo)
# period = '2024-06-16P7D'

# data_payload = {
#     "dataSet": dataSet_id,
#     "period": period,
#     "orgUnit": orgUnit_id,
#     "dataValues": [
#         {"dataElement": dataElement_id, "value": 5}
#     ]
# }

# # Construct the URL for the data value set endpoint
# data_value_set_url = f'{DHIS2_Test_Server_URL}/api/dataValueSets?dryRun=true'
# # Send the POST request with the data payload
# response = requests.post(
#     data_value_set_url,
#     auth=(dhis2_username, dhis2_password),
#     headers={'Content-Type': 'application/json'},
#     data=json.dumps(data_payload)
# )

# # Check the response status
# if response.status_code == 200:
#     print('Data entry dry run successful')
#     print('Response data:')
#     print(response.json())
# else:
#     print(f'Failed to enter data, status code: {response.status_code}')
#     print('Response data:')
#     print(response.json())

# search_items_categoryCombo = ['Polio (OPV) 1 (from 6 wks)']
# item_type = 'dataElements'
# categoryCombos_id = getUID(item_type, search_items_categoryCombo)
