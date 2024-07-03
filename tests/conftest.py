import configparser
from pathlib import Path

import pytest

from msfocr.data.data_upload_DHIS2 import configure_DHIS2_server

@pytest.fixture
def datadir():
    # Path to the directory containing test data
    test_data_dir = Path(__file__).parent / 'data'
    return test_data_dir


@pytest.fixture
def test_server_config(tmp_path): 
    """Configure a mock DHIS2 server to mimic requests. 
    You will still need to use requests_mock to imitate responses from http://test.com.
    """
    config = configparser.ConfigParser()
    config["DHIS2Server"] = {"username": "tester",
                             "password": "testing_password",
                             "server_url": "http://test.com"
                            }
    configpath = tmp_path / "test_settings.ini"
    with configpath.open("w") as configfile:
        config.write(configfile)

    configure_DHIS2_server(configpath)


