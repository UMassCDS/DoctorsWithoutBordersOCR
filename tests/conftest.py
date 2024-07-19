from pathlib import Path

import pytest

import msfocr.data.dhis2

@pytest.fixture
def datadir():
    # Path to the directory containing test data
    test_data_dir = Path(__file__).parent / 'data'
    return test_data_dir


@pytest.fixture
def test_server_config(): 
    """Configure a mock DHIS2 server to mimic requests. 
    You will still need to use requests_mock to imitate responses from http://test.com.
    """
    msfocr.data.dhis2.configure_DHIS2_server("tester", "testing_password", "http://test.com")


