import pytest
import pandas as pd

from msfocr.data import post_processing

def test_generate_key_value_pairs(test_server_config, requests_mock):
    """
    Tests if the dataElement value in the key-value pairs is correct by providing sample tablular data.
    """
    df = pd.DataFrame({
        '0': ['Paed (0-59m) vacc target population'],
        '0-11m': [None],
        '12-59m': [None],
        '5-14y': [None]
    })

    assert len(post_processing.generate_key_value_pairs(df, {'groups': [{'fields':[{"label": "Paed (0-59m) vacc target population 0-11m",
                    "dataElement": "paedid",
                    "categoryOptionCombo": "0to11mid",
                    "type": "INTEGER_POSITIVE"}]}]})) == 0

    df = pd.DataFrame({
        '0': ['BCG', 'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)'],
        '0-11m': ['45+29', None, '30+18'],
        '12-59m': [None, None, '55+29'],
        '5-14y': [None, None, None]
    })
    
    answer = [{'dataElement': 'bcgid', 'categoryOptions': '0to11mid', 'value': '45+29'},
              {'dataElement': 'polioid', 'categoryOptions': '0to11mid', 'value': '30+18'},
              {'dataElement': 'polioid', 'categoryOptions': '5to14yid', 'value': '55+29'}]

    data_element_pairs = post_processing.generate_key_value_pairs(df, 
                    {'groups': [{'fields':[{"label": "BCG 0-11m",
                    "dataElement": "bcgid",
                    "categoryOptionCombo": "0to11mid",
                    "type": "INTEGER_POSITIVE"}]},
                    {'fields':[{"label": "Polio (OPV) 1 (from 6 wks) 0-11m",
                    "dataElement": "polioid",
                    "categoryOptionCombo": "0to11mid",
                    "type": "INTEGER_POSITIVE"}]},
                    {'fields':[{"label": "Polio (OPV) 1 (from 6 wks) 12-59m",
                    "dataElement": "polioid",
                    "categoryOptionCombo": "5to14yid",
                    "type": "INTEGER_POSITIVE"}]}]})
    
    assert len(data_element_pairs) == len(answer)

    for i in range(len(data_element_pairs)):
        assert data_element_pairs[i]['value'] == answer[i]['value']
        
        
def test_evaluate_cells():
    """
    Tests if evaluate_cells works correctly
    """
    df = pd.DataFrame({
        0: ["", "Row 1", "Row 2"],
        1: ["Column 1", "", "-"],
        2: ["Column 2", "", "15"],
        3: ["Column 3", "12+8", "16 - 4"]
    })
    
    answer = pd.DataFrame({
        0: ["", "Row 1", "Row 2"],
        1: ["Column 1", "", "-"],
        2: ["Column 2", "", "15"],
        3: ["Column 3", "20", "12"]
    })
    
    assert post_processing.evaluate_cells([df]) == answer