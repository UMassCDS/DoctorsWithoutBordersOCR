import base64
import json
import os
from openai import OpenAI
from urllib.parse import urlparse

# Initialize OpenAI API client with the provided API key
api_key = ''
client = OpenAI(api_key=api_key)
MODEL = "gpt-4-turbo"


def encode_image(image_path):
    """
    Encode the image at the specified path to a base64 string.
    :param image_path: Path to the image file
    :return: Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def load_json_schema(schema_file: str) -> dict:
    """
    Load a JSON schema from a file.
    :param schema_file: Path to the JSON schema file
    :return: JSON schema as a dictionary
    """
    with open(schema_file, 'r') as file:
        return json.load(file)


def get_image_content(image_path_or_url):
    """
    Get the image content in the required format, either from a URL or a local file.
    :param image_path_or_url: URL or path to the local image file
    :return: A dictionary with the type and corresponding image content
    """
    if os.path.isfile(image_path_or_url):
        # If the path is a file, encode the image as a base64 string
        base64_image = encode_image(image_path_or_url)
        return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
    else:
        # Assume the input is a URL
        return {"type": "image_url", "image_url": {"url": image_path_or_url}}


def main(image_path_or_url):
    """
    Main function to extract text from an image and save the result as JSON.
    :param image_path_or_url: URL or path to the local image file
    :return: Parsed JSON response
    """
    image_content = get_image_content(image_path_or_url)

    # Prepare the prompt with the user message and image content
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": [
                {"type": "text",
                 "text": "Extract the text from the image and separate the table and non-table parts. "
                         "Provide the output in JSON format with two keys: non_table_data and table_data. "
                         "The non_table_data should include all the non-table text, and the table_data should include the table structure and its recognized text. "
                         "Ensure the JSON is formatted correctly for direct saving to a file."


                 },
                image_content
            ]}
        ],
        temperature=0.0,
    )

    # Return the parsed JSON content from the response
    # This is not JSON mode, so parse the returned text accordingly.
    return json.loads(response.choices[0].message.content[7:-4])


if __name__ == "__main__":
    # Image path or URL to be processed
    image_path_or_url = 'IMG_20240514_090947.jpg'

    # Get the extracted and parsed JSON data
    json_data = main(image_path_or_url)
    print(json_data)

    # Generate the output JSON filename based on the input file or URL
    if os.path.isfile(image_path_or_url):
        filename_without_extension = os.path.splitext(os.path.basename(image_path_or_url))[0]
    else:
        filename_without_extension = os.path.splitext(os.path.basename(urlparse(image_path_or_url).path))[0]

    json_filename = f"{filename_without_extension}.json"

    # Save the JSON data to a file
    with open(json_filename, 'w') as file:
        json.dump(json_data, file, indent=4)

    print(f"JSON data saved to {json_filename}")
