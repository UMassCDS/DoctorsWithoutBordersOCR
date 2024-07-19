from msfocr.data.dhis2 import getAllUIDs

def test_getAllUIDs(test_server_config, requests_mock):
    requests_mock.get("http://test.com/api/categoryOptions?filter=name:ilike:12-59m", json={'categoryOptions': [{'id': 'tWRttYIzvBn', 'displayName': '12-59m'}]})
    expected_result = [('12-59m', 'tWRttYIzvBn')]
    result = getAllUIDs("categoryOptions", ["12-59m"])

    assert expected_result == result

