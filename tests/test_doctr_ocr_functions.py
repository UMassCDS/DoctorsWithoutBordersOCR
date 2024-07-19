from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image
from img2table.ocr import DocTR
import pandas as pd

from msfocr.doctr import ocr_functions

def test_get_sheet_type(datadir):
    """
    Tests if the tally sheet type (dataSet, orgUnit, period) detected for a sample image is correct.
    """
    img_path = datadir / 'IMG_20240514_090947.png'
    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    document = DocumentFile.from_images(img_path)
    result = ocr_functions.get_word_level_content(ocr_model, document)

    sheet_type = ocr_functions.get_sheet_type(result)

    assert sheet_type[0] == "Vaccination - paediatric"
    assert sheet_type[1] == "W-14"
    assert sheet_type[2] == ["2024-06-25", "2024-06-30"]


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

    requests_mock.get("http://test.com/api/dataSets/10?fields=dataSetElements", json={'dataSetElements' : [{"categoryCombo": {"id": 5},"dataElement": {"id": 1},"dataSet": {"id": 10}}, {"categoryCombo": {"id": 5},"dataElement": {"id": 3},"dataSet": {"id": 10}}]})
    requests_mock.get("http://test.com/api/categoryCombos/5?fields=categoryOptionCombos", json={"categoryOptionCombos": [{"id": 8}, {"id": 9}]})
    requests_mock.get("http://test.com/api/categoryOptionCombos/8?fields=name", json={"name": "0-11m"})
    requests_mock.get("http://test.com/api/categoryOptionCombos/9?fields=name", json={"name": "12-59m"})
    requests_mock.get("http://test.com/api/dataElements?filter=dataSetElements.dataSet.id:eq:10&fields=id,formName", json={'dataElements': [{'formName': 'BCG','id':1},{'formName': 'Polio (OPV) 1 (from 6 wks)','id':3}]})

    assert len(ocr_functions.generate_key_value_pairs(df, 10)) == 0

    df = pd.DataFrame({
        '0': ['BCG', 'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)'],
        '0-11m': ['45+29', None, '30+18'],
        '12-59m': [None, None, '55+29'],
        '5-14y': [None, None, None]
    })
    
    requests_mock.get("http://test.com/api/dataElements?filter=formName:ilike:BCG", json={"dataElements":[{"id": 1, "displayName": "AVAC_002 BCG"}]})
    requests_mock.get("http://test.com/api/categoryOptions?filter=name:ilike:0-11m", json={'categoryOptions': [{'id': 2, 'displayName': '0-11m'}]})
    requests_mock.get("http://test.com/api/dataElements?filter=formName:ilike:Polio (OPV) 1 (from 6 wks)", json={'dataElements': [{'id': 3, 'displayName': 'AVAC_006 Polio (OPV) 1 (from 6 wks)'}]})
    requests_mock.get("http://test.com/api/categoryOptions?filter=name:ilike:12-59m", json={'categoryOptions': [{'id': 4, 'displayName': '12-59m'}]})

    answer = [{'dataElement': '', 'categoryOptions': '', 'value': '45+29'},
              {'dataElement': '', 'categoryOptions': '', 'value': '30+18'},
              {'dataElement': '', 'categoryOptions': '', 'value': '55+29'}]

    data_element_pairs = ocr_functions.generate_key_value_pairs(df, 10)
    assert len(data_element_pairs) == len(answer)

    for i in range(len(data_element_pairs)):
        assert data_element_pairs[i]['value'] == answer[i]['value']


def test_get_tabular_content(datadir):
    """
    Tests if all tables in a sample image are detected by the ML model.
    Tests if all rows and columns of every table in the sample image is detected correctly.
    """
    img_path = str(datadir / 'IMG_20240514_091004.jpg')
    document = DocumentFile.from_images(img_path)

    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

    result = ocr_functions.get_word_level_content(ocr_model, document)

    confidence_lookup_dict = ocr_functions.get_confidence_values(result)

    doctr_ocr = DocTR(detect_language=False)
    img = Image(src=img_path)  # , detect_rotation=True
    table_df, confidence_df = ocr_functions.get_tabular_content(doctr_ocr, img, confidence_lookup_dict)

    assert len(table_df) == 2

    assert table_df[0].shape == (8,4)
    assert table_df[1].shape == (5,4)