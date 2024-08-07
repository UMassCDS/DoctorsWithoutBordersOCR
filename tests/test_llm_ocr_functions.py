import pytest
from unittest.mock import patch
from typing import Optional
from requests.models import Response
import pandas as pd
from PIL import Image, ImageOps,ExifTags
from io import BytesIO
import base64

import openai
from openai import APIConnectionError, AuthenticationError, APIStatusError

from msfocr.llm import ocr_functions

'Part1-testing llm_ocr_function'
def test_parse_table_data():
    result = {
        'tables': [
            {
                'table_name': 'Paediatric vaccination target group',
                'headers': ['', '0-11m', '12-59m', '5-14y'],
                'data': [['Paed (0-59m) vacc target population', '', '', '']]
            },
            {
                'table_name': 'Routine paediatric vaccinations',
                'headers': ['', '0-11m', '12-59m', '5-14y'],
                'data': [
                    ['BCG', '45+29', '-', '-'],
                    ['HepB (birth dose, within 24h)', '-', '-', '-'],
                    ['HepB (birth dose, 24h or later)', '-', '-', '-'],
                    ['Polio (OPV) 0 (birth dose)', '30+18', '-', '-'],
                    ['Polio (OPV) 1 (from 6 wks)', '55+29', '-', '-'],
                    ['Polio (OPV) 2', '77+19', '8', '-'],
                    ['Polio (OPV) 3', '116+8', '15+3', '-'],
                    ['Polio (IPV)', '342+42', '-', '-'],
                    ['DTP+Hib+HepB (pentavalent) 1', '88+37', '3', '-'],
                    ['DTP+Hib+HepB (pentavalent) 2', '125+16', '14+1', '-'],
                    ['DTP+Hib+HepB (pentavalent) 3', '107+5', '23+6', '-']
                ]
            }
        ],
        'non_table_data': {
            'Health Structure': 'W14',
            'Supervisor': 'BKL',
            'Start Date (YYYY-MM-DD)': '',
            'End Date (YYYY-MM-DD)': '',
            'Vaccination': 'paediatric'
        }
    }

    expected_table_names = [
        'Paediatric vaccination target group',
        'Routine paediatric vaccinations'
    ]

    expected_dataframes = [
        pd.DataFrame([['', '0-11m', '12-59m', '5-14y'], ['Paed (0-59m) vacc target population', '', '', '']]),
        pd.DataFrame([
            ['', '0-11m', '12-59m', '5-14y'],
            ['BCG', '45+29', '-', '-'],
            ['HepB (birth dose, within 24h)', '-', '-', '-'],
            ['HepB (birth dose, 24h or later)', '-', '-', '-'],
            ['Polio (OPV) 0 (birth dose)', '30+18', '-', '-'],
            ['Polio (OPV) 1 (from 6 wks)', '55+29', '-', '-'],
            ['Polio (OPV) 2', '77+19', '8', '-'],
            ['Polio (OPV) 3', '116+8', '15+3', '-'],
            ['Polio (IPV)', '342+42', '-', '-'],
            ['DTP+Hib+HepB (pentavalent) 1', '88+37', '3', '-'],
            ['DTP+Hib+HepB (pentavalent) 2', '125+16', '14+1', '-'],
            ['DTP+Hib+HepB (pentavalent) 3', '107+5', '23+6', '-']
        ])
    ]

    table_names, dataframes = ocr_functions.parse_table_data(result)
    assert table_names == expected_table_names
    for df, expected_df in zip(dataframes, expected_dataframes):
        pd.testing.assert_frame_equal(df, expected_df)


def test_rescale_image():
    # Create a simple image for testing
    img = Image.new('RGB', (3000, 1500), color='red')

    # Test resizing largest dimension
    resized_img = ocr_functions.rescale_image(img, 2048, True)
    assert max(resized_img.size) == 2048
    assert resized_img.size == (2048, 1024)  # Expected resized dimensions

    # Test resizing smallest dimension
    resized_img = ocr_functions.rescale_image(img, 768, False)
    assert min(resized_img.size) == 768
    # 768 / 1024 * 2048 = 1536
    assert resized_img.size == (1536, 768)


def test_encode_image():
    # Create a simple image for testing
    img = Image.new('RGB', (3000, 1500), color='red')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)

    # Encode the image using the encode_image function
    encoded_string = ocr_functions.encode_image(buffered)

    # Verify that the encoded string is a valid base64 string
    decoded_image = base64.b64decode(encoded_string)
    assert decoded_image[:8] == b'\x89PNG\r\n\x1a\n'

    # Optionally, check if the image can be successfully loaded back
    img_back = Image.open(BytesIO(decoded_image))
    assert max(img_back.size) == 2048 or min(img_back.size) == 768


def create_test_image_with_orientation(orientation):
    # Create a simple image
    img = Image.new('RGB', (100, 50), color='red')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    buffered.seek(0)

    # Load the image and manually set the orientation EXIF tag
    img_with_orientation = Image.open(buffered)
    exif = img_with_orientation.getexif()
    exif[274] = orientation  # 274 is the EXIF tag code for Orientation
    exif_bytes = exif.tobytes()

    # Save the image with the new EXIF data
    buffered = BytesIO()
    img_with_orientation.save(buffered, format="JPEG", exif=exif_bytes)
    buffered.seek(0)
    return buffered


def assert_color_within_tolerance(color1, color2, tolerance=1):
    for c1, c2 in zip(color1, color2):
        assert abs(c1 - c2) <= tolerance


def test_correct_image_orientation():
    # Test for orientation 3 (180 degrees)
    img_data = create_test_image_with_orientation(3)
    corrected_image = ocr_functions.correct_image_orientation(img_data)
    assert corrected_image.size == (100, 50)
    # Check if top-left pixel is red after rotating 180 degrees
    assert_color_within_tolerance(corrected_image.getpixel((0, 0)), (255, 0, 0))

    # Test for orientation 6 (270 degrees)
    img_data = create_test_image_with_orientation(6)
    corrected_image = ocr_functions.correct_image_orientation(img_data)
    assert corrected_image.size == (50, 100)
    # Check if bottom-left pixel is red after rotating 270 degrees
    assert_color_within_tolerance(corrected_image.getpixel((0, corrected_image.size[1] - 1)), (255, 0, 0))

    # Test for orientation 8 (90 degrees)
    img_data = create_test_image_with_orientation(8)
    corrected_image = ocr_functions.correct_image_orientation(img_data)
    assert corrected_image.size == (50, 100)
    # Check if top-right pixel is red after rotating 90 degrees
    assert_color_within_tolerance(corrected_image.getpixel((corrected_image.size[0] - 1, 0)), (255, 0, 0))


'Part2-testing openai api call'
class AIHandler:
    MODEL = "gpt-4o"

    def __init__(self, openai_key: str) -> None:
        self.openai_key = openai_key
        openai.api_key = self.openai_key

    def query_api(self, query: str) -> Optional[str]:
        """
        Query the AI API.

        Args:
            query: Query to send to the API
        Returns:
            Response message from the API
        """
        # No need to query the API if there is no query content
        if not query:
            return None

        message = [{"role": "user", "content": query}]

        result = None
        try:
            completion = openai.ChatCompletion.create(
                model=self.MODEL, messages=message
            )
            result = completion.choices[0].message['content']
        except AuthenticationError:
            pass
        except APIConnectionError:
            pass
        except APIStatusError:
            pass
        return result

class MockedChoice:
    def __init__(self, content: str) -> None:
        self.message = {"content": content}

class MockedCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [MockedChoice(content)]

@pytest.fixture
def ai_handler():
    return AIHandler(openai_key="fake_api_key")

@patch('openai.ChatCompletion.create')
def test_query_api(mock_create, ai_handler):
    # Mocking the response from OpenAI API
    mock_create.return_value = MockedCompletion("This is a mocked response from AI.")

    # Call the method with a test query
    response = ai_handler.query_api("Test query")

    # Check that the mocked response is returned
    assert response == "This is a mocked response from AI."

    # Check that the API was called with the correct parameters
    mock_create.assert_called_once_with(
        model="gpt-4o", messages=[{"role": "user", "content": "Test query"}]
    )

@patch('openai.ChatCompletion.create')
def test_query_api_authentication_error(mock_create, ai_handler):
    # Create a mock response object
    mock_response = Response()
    mock_response.status_code = 401  # Unauthorized status code

    # Mock the error
    mock_create.side_effect = AuthenticationError(
        message="Invalid API key",
        response=mock_response,
        body={}
    )

    response = ai_handler.query_api("Test query")

    assert response is None
    mock_create.assert_called_once_with(
        model="gpt-4o", messages=[{"role": "user", "content": "Test query"}]
    )



