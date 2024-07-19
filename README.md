# DoctorsWithoutBorders

Code repository for 2024 Data Science for the Common Good project with Doctors Without Borders.

Doctors Without Borders collects data from their clinics and field locations using tally sheets. These tally sheets are standardized forms containing aggregate data, ensuring no individual can be identified and no protected health information (PHI) is included. Currently, this data is manually entered into their health system by over 100 employees, a time-consuming and tedious process. Our OCR pipeline is designed to automate this data entry process, improving efficiency and accuracy.


# Getting Started
## Installing Dependencies and Packages
Use these steps for setting up a development environment to install and work with code in this template:
1) Set up a Python 3 virtual environment using [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#) or [Virtualenv](https://virtualenv.pypa.io/en/latest/index.html). Read [Python Virtual Environments: A Primer](https://realpython.com/python-virtual-environments-a-primer/#the-virtualenv-project) for details on how to get started with virtual environments and why you need them. For a _really detailed_ explanation, see [An unbiased evaluation of environment management and packaging tools](https://alpopkes.com/posts/python/packaging_tools/). 
2) Activate your virtual environment.
3) Install the package.
	- If you want to just use the scripts and package features, install the project by running `pip install .` from the root directory.
	- If you will be changing the code and running tests, you can install it by running `pip install -e '.[test,dev]'`. The `-e/--editable` flag means local changes to the project code will always be available with the package is imported. You wouldn't use this in production, but it's useful for development.

For example, if you use the 'venv' module, you would run the following to create an environment named `venv` with Python version 3.10, then activate it and install the package in developer mode.
Make sure you have Python 3.10 or later installed on your system. You can check your Python version by running `python3 --version`.
Navigate to your project directory in the terminal and run the following command to create a virtual environment named `venv` - `python3 -m venv venv`.
To activate the virtual environment, use `venv\Scripts\activate` on Windows or `source venv/bin/activate` on Unix or MacOS.
To install the package, run `pip install .` for regular use or `pip install -e .[test,dev]` for development. Ps use `pip install -e '.[test,dev]'` for zsh.


## Instructions for Downloading data from Azure
This part demonstrates how to interact with Azure services to download blobs from Azure Blob Storage.

First, launch Jupyter Notebook:
```bash
jupyter notebook
```
In the Jupyter Notebook interface, navigate to the folder 'notebooks', open the 'ocr_azure_functions' file. Then you can run the cells.
Here are the explanations for the various parameters used in the script.
- **`keyvault_url`**:
  - **Usage**: Connects to the Key Vault.

- **`secret_name`**:
  - **Usage**: Retrieves the secret from the Key Vault.

- **`storage_account_name`**:
  - **Usage**: Constructs the connection string for Blob Storage.

- **`container_name`**:
  - **Usage**: Specifies which container to list or download blobs from.

- **`storage_account_key = get_keyvault_secret(keyvault_url, secret_name, credential)`**:
  - **Usage**: Retrieves the storage account key from the Key Vault using the specified URL, secret name, and credential.
    
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

## Uploading data to a DHIS2 server
This repository assumes assumes you will eventually want to upload data extracted from form images to a [DHIS2 health information server](https://dhis2.org/). In order to configure your connection to the DHIS2, you will need to set the following environment variables:
```
DHIS2_USERNAME=<your username>
DHIS2_PASSWORD=<your password>
DHIS2_SERVER_URL=<server url>
```

If you are using the OpenAI's GPT model as your OCR engine, you will also need to set `OPENAI_API_KEY` with an API key obtained from [OpenAI's online portal](https://platform.openai.com/).

# Tests
This repository has unit tests in the `tests` directory configured using [pytest](https://pytest.org/) and the Github action defined in `.github/workflows/python_package.yml` will run tests every time you make a pull request to the main branch of the repository. 

You can run tests locally using `pytest` or `python -m pytest` from the command line from the root of the repository or configure them to be [run with a debugger in your IDE](https://code.visualstudio.com/docs/python/testing).
