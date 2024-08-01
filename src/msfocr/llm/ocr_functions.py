"""Processing images by working with the OpenAI API. 
Note that the OPENAI_API_KEY environment variable must be set for this module to work correctly. 
This should be done before you run your program. See https://github.com/openai/openai-python for details
""" 
import base64
import json
from concurrent.futures.thread import ThreadPoolExecutor
from io import BytesIO

import pandas as pd

from openai import OpenAI
from PIL import Image, ExifTags

def get_results(uploaded_image_paths):
    """
    Processes uploaded image paths using the OpenAI API and returns the results.

    Usage:
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    results = get_results(image_paths)

    :param uploaded_image_paths: List of uploaded image file paths.
    :return: List of results from the OpenAI API.
    """
    '''
    results = []
    for img_path in uploaded_image_paths:
        result = extract_text_from_image(img_path)
        results.append(result)
    '''

    return extract_text_from_batch_images(uploaded_image_paths)


def parse_table_data(result):
    """
    Parses table data from the OpenAI API results into DataFrames.

    Usage:
    table_names, dataframes = parse_table_data(api_result)

    :param result: Result from the GPT-4o API containing table data.
    :return: Tuple containing a list of table names and a list of DataFrames parsed from the table data.
    """
    table_data = result["tables"]
    table_names = []
    dataframes = []

    for table in table_data:
        table_name = table.get("table_name", f"Table {len(dataframes) + 1}")
        columns = table["headers"]
        data = table["data"]
        data.insert(0, columns)
        df = pd.DataFrame(data)
        table_names.append(table_name)
        dataframes.append(df)

    return table_names, dataframes


def rescale_image(img, limit, maxi=True):
    width, height = img.size
    if maxi:
        max_dim = max(width, height)
    else:
        max_dim = min(width, height)
    if max_dim > limit:
        scale_factor = limit / max_dim
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        img = img.resize((new_width, new_height))
    return img


def encode_image(image_path):
    """
    Encodes an image file to base64 string.

    Usage:
    base64_string = encode_image(image_file)

    :param image_path: File object of the image to encode.
    :return: Base64 encoded string of the image.
    """
    image_path.seek(0)
    with Image.open(image_path) as img:
        img = rescale_image(img, 2048, True)
        img = rescale_image(img, 768, False)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def extract_text_from_image(image_path):
    """
    Extracts text and table data from an image using OpenAI's GPT-4 vision model.

    Usage:
    result = extract_text_from_image("path/to/image.jpg")

    :param image_path: Path to the image file.
    :return: JSON object containing extracted text and table data.
    """
    client = OpenAI()
    MODEL = "gpt-4o"
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": [
                {"type": "text",
                 "text": "Analyze this image as a completely new task. "
                         "Identify and parse all tables and non-table data. "
                         "For each table, carefully examine and transcribe its name from the image, typically located at the top left of the table. "
                         "If the table name is unclear or missing, label it 'Table X' where X is a sequential number. "
                         "Do not use any previously identified table names. "
                         "Apply image corrections if needed for better text recognition. "
                         "Construct each table with its newly identified name, columns, and rows, extracting all visible numbers. "
                         "Format JSON with two main objects: 1) 'tables': an array of table objects {'table_name': '...', 'headers': [...], 'data': [[...], ...]}, 2) 'non_table_data': an object with key-value pairs for all non-table information. "
                         "Respond only with the JSON: {'tables': [...], 'non_table_data': {...}}. "
                         "No explanations. "
                         "Treat this as an entirely new image with no relation to any previous tasks."

                 },
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                 }
            ]}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def extract_text_from_batch_images(image_paths):
    """
    Extracts text and table data from multiple images using OpenAI's GPT-4 omni model.
    This version processes images concurrently using multithreading.

    Usage:
    results = extract_text_from_images(["path/to/image1.jpg", "path/to/image2.jpg"])

    :param image_paths: List of paths to the image files.
    :return: List of JSON objects containing extracted text and table data for each image.
    """
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(extract_text_from_image, image_paths))
    return results

def correct_image_orientation(image_path):
    """
    Corrects the orientation of an image based on its EXIF data.

    Usage:
    corrected_image = correct_image_orientation("path/to/image.jpg")

    :param image_path: The path to the image file.
    :return: PIL.Image.Image: The image with corrected orientation.
    """
    image = Image.open(image_path)
    orientation = None
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image.getexif().items())
        if exif.get(orientation) == 3:
            image = image.rotate(180, expand=True)
        elif exif.get(orientation) == 6:
            image = image.rotate(270, expand=True)
        elif exif.get(orientation) == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image


