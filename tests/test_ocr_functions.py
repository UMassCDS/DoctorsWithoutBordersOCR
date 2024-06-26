from docTR import ocr_functions
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image
from img2table.ocr import DocTR
import os
import pandas as pd


def test_get_sheet_type():
    current_dir = os.path.dirname(__file__)
    img_path = os.path.join(current_dir, '..', 'data', 'MSF_data', 'IMG_20240514_090947.png')

    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    document = DocumentFile.from_images(img_path)
    result = ocr_functions.get_word_level_content(ocr_model, document)

    sheet_type = ocr_functions.get_sheet_type(result)

    assert sheet_type[0] == "Vaccination - paediatric"
    assert sheet_type[1] == "W-14"
    assert sheet_type[2] == ["2024-06-25", "2024-06-30"]


def test_generate_key_value_pairs():
    df = pd.DataFrame({
        '0': ['Paed (0-59m) vacc target population'],
        '0-11m': [None],
        '12-59m': [None],
        '5-14y': [None]
    })

    assert len(ocr_functions.generate_key_value_pairs(df)) == 0

    df = pd.DataFrame({
        '0': ['BCG', 'HepB (birth dose, within 24h)', 'HepB (birth dose, 24h or later)',
              'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)'],
        '0-11m': ['45+29', None, None, '30+18', '55+29'],
        '12-59m': [None, None, None, None, None],
        '5-14y': [None, None, None, None, None]
    })

    answer = [{'dataElement': '', 'categoryCombo': '', 'value': '45+29'},
              {'dataElement': '', 'categoryCombo': '', 'value': '30+18'},
              {'dataElement': '', 'categoryCombo': '', 'value': '55+29'}]

    data_element_pairs = ocr_functions.generate_key_value_pairs(df)
    assert len(data_element_pairs) == len(answer)

    for i in range(len(data_element_pairs)):
        assert data_element_pairs[i]['value'] == answer[i]['value']


def test_get_tabular_content():
    current_dir = os.path.dirname(__file__)
    img_path = os.path.join(current_dir, '..', 'data', 'MSF_data', 'IMG_20240514_090947.png')
    document = DocumentFile.from_images(img_path)

    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

    result = ocr_functions.get_word_level_content(ocr_model, document)

    confidence_lookup_dict = ocr_functions.get_confidence_values(result)

    doctr_ocr = DocTR(detect_language=False)
    img = Image(src=img_path)  # , detect_rotation=True
    table_df, confidence_df = ocr_functions.get_tabular_content(doctr_ocr, img, confidence_lookup_dict)

    assert len(table_df) == 2

    assert table_df[0].shape == (2,4)
    assert table_df[1].shape == (12,4)