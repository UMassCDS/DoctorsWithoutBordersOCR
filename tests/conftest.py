import pytest
from pathlib import Path

@pytest.fixture
def datadir(request):
    # Path to the directory containing test data
    test_data_dir = Path(__file__).parent / 'data'
    return test_data_dir
