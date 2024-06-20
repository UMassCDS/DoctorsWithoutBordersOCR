import json
import time
import base64
import warnings
import streamlit as st
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

# Ignore any warnings
warnings.filterwarnings("ignore")

# Title of the Streamlit app
st.title("Image to Text App")

def putMarkdown():
    # Function to add a horizontal line in the app
    st.markdown("<hr>", unsafe_allow_html=True)

def get_download_button(data, button_text, filename):
    # Function to create a download button for JSON data
    json_str = json.dumps(data, indent=4)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;charset=utf-8;base64,{b64}" download="{filename}">{button_text}</a>'
    return href

def ocr(item):
    # Function to perform OCR on the given item
    model = ocr_predictor("db_resnet50", "crnn_vgg16_bn", pretrained=True)
    result = model(item)
    json_output = result.export()
    return result, json_output

def display(result, json_output, img):
    # Function to display the OCR results in the app
    st.write("#### Download JSON output")
    st.write("*⬇*" * 9)

    # Create and display a download button for the JSON output
    download_button_str = get_download_button(json_output, "DOWNLOAD", "data.json")
    st.markdown(download_button_str, unsafe_allow_html=True)
    putMarkdown()

    # Display the original image
    st.image(img, caption="Original image")
    putMarkdown()

    # Generate and display synthetic pages from the OCR result
    synthetic_pages = result.synthesize()
    st.image(synthetic_pages, caption="Result of image")

    # Calculate and display the elapsed time
    elapsed_time = time.time() - start_time
    putMarkdown()

    # Extract and display the OCR results in various formats
    whole_words = []
    per_line_words = []
    for block in json_output["pages"][0]["blocks"]:
        for line in block["lines"]:
            line_words = []
            for word in line["words"]:
                whole_words.append(word["value"])
                line_words.append(word["value"])
            per_line_words.append(line_words)

    # Display all the words
    st.write("## Whole Words:")
    st.write(" ".join(whole_words))
    putMarkdown()

    # Display words line by line
    st.write("## Line by Line:")
    for line_words in per_line_words:
        st.write(" ".join(line_words))
    putMarkdown()

    # Display words individually
    st.write("## Word by Word:")
    for index, item in enumerate(whole_words):
        st.write(f"**Word {index}**:", item)
    putMarkdown()

    # Display success message with elapsed time
    st.write(f"Successful! Passed Time: {elapsed_time:.2f} seconds")

def main():
    global start_time, seconds_elapsed, stop_time

    # Uploading an image file
    uploaded_file = st.file_uploader("Choose a File", type=["jpg", "jpeg", "png", "pdf"])

    st.write("#### or Put an URL")
    url = st.text_input("Please type an URL:")

    if st.button("Show The URL"):
        # OCR from a URL
        st.write("Typed URL:", url)
        start_time = time.time()

        single_img_doc = DocumentFile.from_url(url)
        result, json_output = ocr(single_img_doc)
        display(result, json_output)

    elif uploaded_file is not None:
        # OCR from an uploaded file
        start_time = time.time()

        if uploaded_file.type == "application/pdf":
            image = uploaded_file.read()
            single_img_doc = DocumentFile.from_pdf(image)
        else:
            image = uploaded_file.read()
            single_img_doc = DocumentFile.from_images(image)

        result, json_output = ocr(single_img_doc)
        display(result, json_output, image)

if __name__ == "__main__":
    main()
