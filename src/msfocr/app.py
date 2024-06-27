import streamlit as st
import pandas as pd
import json
import numpy as np
import io

from streamlit.elements.image import PILImage

import data.data_upload_DHIS2 as dhis2
from docTR.ocr_functions import (get_word_level_content, get_confidence_values,
                           get_tabular_content, get_sheet_type, generate_key_value_pairs)
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image
from img2table.ocr import DocTR

# Initializing variables
form_types = ("ICCM", "OPD", "RHGynobs", "Vaccination")


# Function definitions
@st.cache_data
def data_values(df):
    data_values = []
    columns = df.columns.tolist()
    for col, i in df.iterrows():
        for cell in columns:
            if i[cell] is not None:
                new_cell = {"dataElement": f"{col}/{cell}", "value": f"{i[cell]}"}
                data_values.append(new_cell)
    return data_values


@st.cache_data
def dhis2_all_UIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL):
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL)


def convert_df(dfs):
    json_export = {}
    if data_set == "":
        data_set_id = ""
    else:
        data_set_id = dict(data_set_options)[data_set_dropdown]
    json_export["dataSet"] = f"{data_set_id}"
    json_export["period"] = f"{period_start}P7D"
    if org_unit == "":
        org_unit_id = ""
    else:
        org_unit_id = dict(org_unit_options)[org_unit_dropdown]
    json_export["orgUnit"] = f"{org_unit_id}"
    data_values_list = []
    for df in dfs.values():
        data_values_list += data_values(df)
    json_export["dataValues"] = data_values_list
    return json.dumps(json_export)


# Initial Display
st.title("MSF OCR Tool")
st.write("### File Upload ###")
tally_sheet = st.file_uploader("Please upload one or more images of a tally sheet", type=["png", "jpg", "jpeg"],
                               accept_multiple_files=True)

# Displaying images so the user can see them
with st.expander("Show Images"):
    for sheet in tally_sheet:
        st.image(sheet)

# OCR Model
ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

# Once images are uploaded
if len(tally_sheet) > 0:    # Will have prefilled data when OCR works
    form_type = st.selectbox(
        "Which type of form is this?",
        form_types,
        index=None
    )
    org_unit = st.text_input("Organization Unit:")

    org_unit_options = dhis2_all_UIDs("organisationUnits", org_unit, **st.secrets.dhis2_credentials)
    org_unit_dropdown = st.selectbox(
        "Searched Organizations",
        [id[0] for id in org_unit_options],
        index=None
    )
    data_set = st.text_input("Data Set:")
    data_set_options = dhis2_all_UIDs("dataSets", data_set, **st.secrets.dhis2_credentials)
    data_set_dropdown = st.selectbox(
        "Searched Datasets",
        [id[0] for id in data_set_options],
        index=None
    )
    period_start = st.date_input("Period Start Date:", format="YYYY-MM-DD")
    period_end = st.date_input("Period End Date:", format="YYYY-MM-DD")

    uploaded_images = [DocumentFile.from_images(sheet.read()) for sheet in tally_sheet]
    results = [get_word_level_content(ocr_model, doc) for doc in uploaded_images]

    # Display OCR results
    for i, result in enumerate(results):
        st.write(f"OCR Result for Image {i + 1}:")
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    st.write(" ".join(word.value for word in line.words))

    for result in results:
        confidence_lookup_dict = get_confidence_values(result)
        doctr_ocr = DocTR(detect_language=False)
        table_dfs = []
        for sheet in tally_sheet:
            img = Image(src=sheet)
            table_df, confidence_df = get_tabular_content(doctr_ocr, img, confidence_lookup_dict)
            table_dfs.append(table_df)

        # # Display detected tables
        # if table_dfs:
        #     st.write("### Detected Tables ###")
        #     for i, df in enumerate(table_dfs):
        #         st.write(f"Table {i + 1}")
        #         st.dataframe(pd.DataFrame(df))

        # Assuming the form_type is "ICCM" for simplicity
        form_type = "ICCM"
        if form_type == "ICCM":
            dfs = [
                pd.DataFrame({'2-5m': [None, None, None, None, None, None, None, None, None, None],
                              '6-59m': [None, None, None, None, None, None, None, None, None, None],
                              '5-14y': [None, None, None, None, None, None, None, None, None, None],
                              ">=15y": [None, None, None, None, None, None, None, None, None, None]},
                             index=["No. of consultations", "Patients treated repeat past 28d",
                                    "No. of patients with RDT performed", "No. RDT+: P. falciparum",
                                    "No. RDT+: P. falciparum and/or mixed", "No. RDT+: non P. falciparum",
                                    "RDT+ treated with ACT past 28 days", "No. of patients with danger signs",
                                    "No. with bloody diarrhoea", "No. with acute watery diarrhoea"]),
                pd.DataFrame({'6-59m': [None, None, None, None]},
                             index=["Bilateral oedema", "MUAC SAM", "MUAC MAN", "MUAC no AM"]),
                pd.DataFrame({'2-5m': [None, None, None, None, None, None, None, None, None, None, None, None],
                              '6-59m': [None, None, None, None, None, None, None, None, None, None, None, None],
                              '5-14y': [None, None, None, None, None, None, None, None, None, None, None, None],
                              ">=15y": [None, None, None, None, None, None, None, None, None, None, None, None]},
                             index=["Uncomplicated malaria", "Suspected severe malaria", "Uncomplicated pneumonia",
                                    "Uncomplicated diarrhoea", "Cough/cold", "Severe acute malnutrition",
                                    "Other (uncomplicated)", "Other (severe)", "Malaria with severe acute malnutrition",
                                    "Malaria with pneumonia", "Malaria with diarrhoea", "Other combination"]),
                pd.DataFrame(
                    {'2-5m': [None, None, None, None, None, None], '6-59m': [None, None, None, None, None, None],
                     '5-14y': [None, None, None, None, None, None], ">=15y": [None, None, None, None, None, None]},
                    index=["No. treated ACT 1st line", "No. treated ACT 2nd line",
                           "No. treated pre-referral artesunate", "No. of patients referred", "No. treated antibiotics",
                           "No. treated ORS/Albendazole/Zn"]),
                pd.DataFrame({'<5y': [None, None], '>=5y': [None, None]}, index=["No. patients with bednets at home",
                                                                                 "No. patients that slept under a bednet last night"])
            ]
            titles = [
                "Initial Assessment",
                "Malnutrition",
                "Diagnoses",
                "Treatment",
                "Bednets"
            ]

            # Displaying the editable information
            df_index = 0
            edited_dfs = {}
            for df in dfs:
                st.write(titles[df_index])
                edited_dfs[df_index] = st.data_editor(df, key=df_index)
                df_index += 1

            # Download JSON, will eventually run the submission
            st.download_button(
                label="Download data as JSON",
                data=convert_df(edited_dfs),
                file_name="results.json",
                mime="application/json"
            )

            # Generate and display key-value pairs
            if st.button("Generate Key-Value Pairs"):
                key_value_pairs = []
                for df in edited_dfs.values():
                    key_value_pairs.extend(generate_key_value_pairs(df))
                st.write("### Key-Value Pairs ###")
                st.json(key_value_pairs)
