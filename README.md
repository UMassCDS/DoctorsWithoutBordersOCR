# DoctorsWithoutBordersOCR
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Installation](#installing-dependencies-and-packages)
  - [Streamlit Application](#streamlit-application)
- [Tests](#tests)
- [Extras](#extras)
  - [Docker Instructions](#docker-instructions)
  - [Downloading Test Data from Azure](#downloading-test-data-from-azure)

# Introduction
Code repository for 2024 Data Science for the Common Good project with Doctors Without Borders.

Doctors Without Borders collects data from their clinics and field locations using tally sheets. These tally sheets are standardized forms containing aggregate data, ensuring no individual can be identified and no protected health information (PHI) is included. Currently, this data is manually entered into their health system by over 100 employees, a time-consuming and tedious process. Our OCR pipeline is designed to automate this data entry process, improving efficiency and accuracy.


# Getting Started
## Installing Dependencies and Packages
Use these steps for setting up a development environment to install and work with code in this template:
1) Set up a Python 3 virtual environment using [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#) or [Virtualenv](https://virtualenv.pypa.io/en/latest/index.html). Read [Python Virtual Environments: A Primer](https://realpython.com/python-virtual-environments-a-primer/#the-virtualenv-project) for details on how to get started with virtual environments and why you need them. For a _really detailed_ explanation, see [An unbiased evaluation of environment management and packaging tools](https://alpopkes.com/posts/python/packaging_tools/). 
2) Activate your virtual environment.
3) Install the package.
	  - **Only base package**: If you want to just use the scripts and package features, install the project by running `pip install .` from the root directory.
    - **Package with Streamlit app**: To also install dependencies for the Streamlit frontend application, run `pip install .[app]`.
    - **All development dependencies**: If you will be changing the code and running tests, you can install it by running `pip install -e '.[app,test,dev]'`. The `-e/--editable` flag means local changes to the project code will always be available with the package is imported. You wouldn't use this in production, but it's useful for development. *PS*: use `pip install -e '.[app,test,dev]'` with the quote symbols for zshell/zsh (default shell on newer Macs).

For example, if you use the 'venv' Virtualenv module, you would do the following to create an environment named `venv` with Python version 3.10, then activate it and install the package in developer mode:
  - Make sure you have Python 3.10 or later installed on your system. You can check your Python version by running `python3 --version`.
  - Navigate to your project directory in the terminal and run the following command to create a virtual environment named `venv` - `python3 -m venv venv`.
  - To activate the virtual environment, use `venv\Scripts\activate` on Windows or `source venv/bin/activate` on Unix or MacOS.
  - To install the package, run `pip install .` for regular use or `pip install -e .[test,dev]` for development. 


## Streamlit Application
Uses a Streamlit web app in conjunction with an Optical Character Recognition (OCR) library to allow users to upload documents, scan them, and correct information.

This repository contains two version of the application:
- `app_llm.py` uses [OpenAI's GPT 4o model](https://platform.openai.com/docs/guides/vision) as an OCR engine to 'read' the tables from images
- `app_doctr.py` uses a the [docTR](https://pypi.org/project/python-doctr/) library as an OCR engine to parse text from the tables in images.

### Application configuration 
#### DHIS2 Server
In order to use the application, you will need to set the `DHIS2_SERVER_URL` environment variable. All users will also need a valid username and password for the DHIS2 server in order to authenticate and use the Streamlit application. 

#### OpenAI API Key
If you are using the `app_llm.py` version of the application, you will also need to set `OPENAI_API_KEY` with an API key obtained from [OpenAI's online portal](https://platform.openai.com/).

### Running Streamlit Locally
1) Set your environment variables as described just above. On a unix system the easiest way to do this is put them in a `.env` file, then run `set -a && source .env && set +a`. You can also set them in your System Properties or shell environment profile.  

2) Install the python dependencies with `pip install .[app]`.

3) Run your desired Streamlit application with one of the following commands:
    - OpenAI version: `streamlit run app_llm.py` 
    - DocTR version: `streamlit run app_doctr.py`


# Tests
This repository has unit tests in the `tests` directory configured using [pytest](https://pytest.org/) and the Github action defined in `.github/workflows/python_package.yml` will run tests every time you make a pull request to the main branch of the repository. 

If you have installed the `test` dependencies, you can run tests locally using `pytest` or `python -m pytest` from the command line from the root of the repository or configure them to be [run with a debugger in your IDE](https://code.visualstudio.com/docs/python/testing).


# Extras
## Docker Instructions
We have provided a Dockerfile in order to easily build and deploy the OpenAI version of the Streamlit application as a Docker container. 

1) Build an image named `msf-streamlit`: `docker build -t msf-streamlit .`.

2) Run the `msf-streamlit` image in a container, passing the necessary environment variables: 
    ```bash
    docker run -p 8501:8501 -e DHIS2_USERNAME=<your username> -e DHIS2_PASSWORD=<your password> -e DHIS2_SERVER_URL=<server url> -e OPENAI_API_KEY=<your key> msf-streamlit
    ```

    If you have a `.env` file, you can keep things simple with `docker run -p 8501:8501 --env-file .env msf-streamlit`. 

    Make sure port 8501 is available, as it is the default for Streamlit.

## Downloading Test Data from Azure
This part demonstrates how to interact with Azure services to download blobs from Azure Blob Storage. Do this if you need to download test images of tally sheets from Azure Blob storage. 

First, install the `dev` dependencies, then launch Jupyter Notebook:
```bash
jupyter notebook
```
In the Jupyter Notebook interface, navigate to the folder 'notebooks', open the 'ocr_azure_functions' file. You will need to get the values for the following credentials from someone on the team, fill in the variables in the notebook, then run the cells.
- **`keyvault_url`**: Connects to the Key Vault.

- **`secret_name`**: Retrieves the secret from the Key Vault.

- **`storage_account_name`**: Constructs the connection string for Blob Storage.

- **`container_name`**: Specifies which container to list or download blobs from.

- **`storage_account_key = get_keyvault_secret(keyvault_url, secret_name, credential)`**:  Retrieves the storage account key from the Key Vault using the specified URL, secret name, and credential.
    
### Example Usage
Please specify where to store downloaded files on your computer using the local_path variable.
```bash
keyvault_url = '<keyvault-url>'
secret_name = '<secret-name>'
storage_account_name = "<storage-account-name>"
container_name = "<container-name>"

# Obtain Azure credentials
credential = get_az_credential()

# Retrieve the storage account key from Azure Key Vault
storage_account_key = get_keyvault_secret(keyvault_url, secret_name, credential)

# List blobs in the container
list_blobs_in_container(storage_account_name, storage_account_key, container_name)

# Download blobs in the container
download_blobs_in_container(storage_account_name, storage_account_key, container_name)
```




