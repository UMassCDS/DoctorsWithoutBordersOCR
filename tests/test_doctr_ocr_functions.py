from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image
from img2table.ocr import DocTR

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
    table_df = ocr_functions.get_tabular_content(doctr_ocr, img)

    assert len(table_df) == 2

    assert table_df[0].shape == (8,4)
    assert table_df[1].shape == (5,4)