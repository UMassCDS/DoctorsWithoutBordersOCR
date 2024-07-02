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

   
For example, if you use Conda, you would run the following to create an environment named `template` with python version 3.10, then activate it and install the package in developer mode:
```
$ conda create -n template python=3.10 -y
Collecting package metadata (current_repodata.json): done
Solving environment: done

## Package Plan ##

  environment location: /home/virginia/miniconda3/envs/template

  added / updated specs:
    - python=3.10



The following NEW packages will be INSTALLED:

    package                    |            build
    ---------------------------|-----------------
...

$ conda activate `template`
$ pip install -e .[test,dev]
Obtaining file:///home/virginia/workspace/PythonProjectTemplate
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Installing backend dependencies ... done
    Preparing wheel metadata ... done
Collecting numpy
...
```

## Instructions for Downloading data from azure
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





## Specifying Requirements
In order for users to install your package and all the libraries it depends on by running `pip install`, you need to provide a `pyproject.toml` file. This has two important sections:
- `project`: List project metadata and version information and all library requirements/dependencies, including for testing or development environments. This is the main file you will work with and add requirements to. Some dependencies 
- `build-system`: Define the build tool that is used to package and distribute your code. For this project, we use [SetupTools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).

If you'd like to learn more about python packaging, refer to [the Python Packaging User Guide](https://packaging.python.org/en/latest/) or [PEP 517](https://peps.python.org/pep-0517/#build-requirements).

### Requirements via conda environment files
[Anaconda](https://www.anaconda.com/download/) and its bare bones counterpart, [Miniconda](https://docs.anaconda.com/free/miniconda/index.html), are especially useful if your project depends on libraries that are difficult to install in the standard pythonic way, such as [GPU libraries](https://docs.anaconda.com/free/working-with-conda/packages/gpu-packages/). If this is the case, you should also share a [Conda environment file](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually) with your code. The conda virtual environment will need to be created and activated before any `pip install` steps. Installations with conda dependencies are usually a little more complicated, so make sure you include step-by-step instructions in documentation. 

### Containerized applications
In cases when its important that your software work exactly the same on every operating system or you want to abstract away difficult installation steps for end user, you can consider creating a [Docker container](https://www.docker.com/resources/what-container/). This is often appropriate deploying services in the cloud or providing an application for a tech-savvy person to use on their own. However, it's not necessary for most of our projects. 


## Directory Structure
So what does each file in this repository do?
```
.
├── src
    ├── cdstemplate     # The python package root - Any code you'd like to be able to import lives here
        ├── corpus_counter_script.py    # A script that takes a list of documents as input and outputs a CSV of word counts
        ├── __init__.py     # Indicates that this directory is a python package, you can put special import instructions here
        ├── word_count.py    # A module that has functions and classes to import
        └── utils.py    # A module that handles logging and other internals
├── CHANGELOG.md    # Versioning information
├── dag_workflow.png    # An image that is linked to in this README
├── data    # Data files which may or may not be tracked in Git, but we reserve a folder for them so that users can all have the same relative paths
    ├── gutenberg     # Sample text input files, the raw inputs to our experiment pipeline.
    └── gutenberg_counts.csv     # The expected output file for our experiment. It's generated by `dvc repro` and is ignored by git.
├── docs     # Sphinx auto-documentation uses this folder to run its scripts and store documentation
    ├── _build     # Contains the Sphinx doctree and html documentation source code
        ├── doctrees     # A folder with doctree construction information
        └── html   # A folder that contains the html code for all automatically created documentation
    ├── _static     # A folder that can contain static code
    ├── _templates    # A folder that can contain Sphinx templates
    ├── conf.py    # A function that configures Sphinx according to user specifications  
    ├── index.rst    # A directory that users can input new functions into for auto-documentation
    ├── make.bat    # A function that runs auto-documentation
    └── Makefile    # A function that creates html documentation based on functions in the index.rst file
├── dvc.lock    # Data Version Control uses this file to compare experiment versions. It's tracked in Git, but don't edit it manually.
├── dvc.yaml    # Create the Data Version Control pipeline stages here
├── notebooks
    └── word_count_prototype.ipynb    # A jupyter notebook that makes pretty plots
├── pyproject.toml    # Project metadata, dependencies and build tools are declared for proper installation and packaging.
├── README.md     # You're reading it now!
└── tests
    └── test_word_count.py    # Unit and smoke tests for the word_count module
├── .dvc    # The configuration file for Data Version Control
├── .github
    └── workflows/python_package.yml    # Github Workflow file, configures running tests on Github every time a pull request to the main branch is made
├── .gitignore   # Lists files that should not be included in version control, created from Github's template .gitignore for Python.
└── .dvcignore    # Lists files that Data Version Control should skip when checking for changes in stage dependencies.
```


# Communication Tools and Code
When you work with others, it's not just about the code!

The README, CHANGELOG and docstrings are just as important.

- _README.md_ : Summarize the project's purpose and give installation instructions.
- _CHANGELOG.md_ : Tell the user what has changed between versions and why, see [Keep A CHANGELOG](https://keepachangelog.com/en/1.0.0/)
- docstrings: Appear directly in your code and give an overview of each function or object. They can be printed using `help(object)` from the python interpreter or used to automatically generate API documentation with a tool like [Sphinx](https://www.sphinx-doc.org/en/master/index.html). There are many different docstring formats. Your team can choose any they like, just be consistent. This template uses [reStructuredText style](https://peps.python.org/pep-0287/).
- Sphinx  : Create html documentation for your functions based on the docstrings you write in the code. Use [Sphinx](https://www.sphinx-doc.org/en/master/index.html) to streamline the documentation process.

Read [Real Python's Documenting Python Code: A Complete Guide](https://realpython.com/documenting-python-code/) for more ideas about effectively documenting code. The `.md` files are written using [Markdown](https://www.markdownguide.org/), a handy formatting language that is automatically rendered in Github.

# Tests
Although it's [impossible to generally prove that your code is bug-free](https://en.wikipedia.org/wiki/Undecidable_problem), automated testing is a valuable tool. It provides:
- Proof that your code works as intended in most common examples and important edge cases
- Instant feedback on whether changes to the code broke its functionality
- Examples of how to use the code, a type of documentation

This repository has tests configured using [pytest](https://pytest.org/) and the Github action defined in `.github/workflows/python_package.yml` will run tests every time you make a pull request to the main branch of the repository. [Unittest](https://docs.python.org/3/library/unittest.html#module-unittest) and [nose2](https://docs.nose2.io/en/latest/) are other common test frameworks for python.

You can run tests locally using `pytest` or `python -m pytest` from the command line from the root of the repository or configure them to be [run with a debugger in your IDE](https://code.visualstudio.com/docs/python/testing). For example:
```
$ pytest
======================== test session starts ========================
platform linux -- Python 3.10.4, pytest-7.1.2, pluggy-1.0.0
rootdir: /home/virginia/workspace/PythonProjectTemplate
collected 2 items

tests/test_sample_module.py .
```

Read the following articles for tips on writing your own tests:
- [Getting Started With Testing in Python](https://realpython.com/python-testing/)
- [13 Tips for Writing Useful Unit Tests](https://betterprogramming.pub/13-tips-for-writing-useful-unit-tests-ca20706b5368)
- [Why Good Developers Write Bad Unit Tests](https://mtlynch.io/good-developers-bad-tests)

# Reproducible Experiments
In practice, data science often relies on pipelining many operations together to prepare data, extract features, then train and evaluate models or produce analysis. Whether someone can reproduce your experiments depends on how clearly you lay out the pipeline and parameters that you use for each 'node' in the pipeline, including stating where to find the input data and how it should be formatted.

In practice, you should write scripts that are flexible enough to change the parameters you'd like to experiment with and define the pipeline using a directed acyclic graph (DAG), where the outputs from earlier steps become the dependencies for later ones. It's good practice to draw out the DAG for your experiment first, noting inputs, outputs and parameters, before you code scripts for the pipeline, like this:

![DAG diagram](./dag_workflow.png)

## Reusable Scripts
Our 'experiment' here is simply counting the occurrence of words from a set of documents, in the form of text files, then writing the counts of each word to a CSV file. This operation is made available to users via the `cdstemplate.corpus_counter_script` and by using the [`argparse` command-line parsing library](https://docs.python.org/3/library/argparse.html#module-argparse), we clearly describe the expected input parameters and options, which can be displayed using the `--help` flag. There are [other command-line parsers](https://realpython.com/comparing-python-command-line-parsing-libraries-argparse-docopt-click/) you can use, but `argparse` comes with python, so you don't need to add an extra requirement.


Since we have made the package installable and defined it as the `corpus-counter` script in `project.toml`, users can run it using `corpus-counter`, `python -m cdstemplate.corpus_counter_script` or `python src/cdstemplate/corpus_counter_script.py`, but all work the same way:
```
$ corpus-counter --help 
usage: corpus-counter [-h] [--case-insensitive] csv documents [documents ...]

A script to generate counts of tokens in a corpus

positional arguments:
  csv                   Path to the output CSV storing token counts. Required.
  documents             Paths to at least one raw text document that make up the corpus. Required.

options:
  -h, --help            show this help message and exit
  --case-insensitive, -c
                        Default is to have case sensitive tokenization. Use this flag to make the token counting
                        case insensitive. Optional.
$ python src/cdstemplate/corpus_counter_script.py --help
usage: corpus_counter_script.py [-h] [--case-insensitive]
...
$ python -m cdstemplate.corpus_counter_script --help
usage: corpus_counter_script.py [-h] [--case-insensitive]
                                csv documents [documents ...]

A script to generate counts of tokens in a corpus
...
```

Using the help message, we can understand how to run the script to count all the words in the text files in `data/gutenberg` in a case-insensitive way, saving word counts to a new csv file, `data/gutenberg_counts.csv`:
```
$ corpus-counter data/gutenberg_counts.csv data/gutenberg/*.txt --case-insensitive
INFO : 2023-12-08 12:26:10,770 : cdstemplate.corpus_counter_script : Command line arguments: Namespace(csv='data/gutenberg_counts.csv', documents=['data/gutenberg/austen-emma.txt', 'data/gutenberg/austen-persuasion.txt', 'data/gutenberg/austen-sense.txt', 'data/gutenberg/bible-kjv.txt', 'data/gutenberg/blake-poems.txt', 'data/gutenberg/bryant-stories.txt', 'data/gutenberg/burgess-busterbrown.txt', 'data/gutenberg/carroll-alice.txt', 'data/gutenberg/chesterton-ball.txt', 'data/gutenberg/chesterton-brown.txt', 'data/gutenberg/chesterton-thursday.txt'], case_insensitive=True)
DEBUG : 2023-12-08 12:26:10,771 : cdstemplate.word_count : CorpusCounter instantiated, tokenization pattern: \s, case insensitive: True
INFO : 2023-12-08 12:26:10,771 : cdstemplate.corpus_counter_script : Tokenizing document number 0: data/gutenberg/austen-emma.txt
DEBUG : 2023-12-08 12:26:10,771 : cdstemplate.word_count : Tokenizing '[Emma by Jane Austen 1816]
...
```

## Data Dependencies Tools
[Build automation tools](https://en.wikipedia.org/wiki/Build_automation) like [Make](https://en.wikipedia.org/wiki/Make_(software)) have been used to resolve dependencies and compile software since the 1970s. Build automation can also be used in data science and machine learning workflows for [many of the same reasons](https://en.wikipedia.org/wiki/Build_automation#Advantages), like eliminating redundant tasks, maintaining history and improved quality and consistency through automating processes. Using a build tool can also be a documentation and communication tool, since it declares the most common ways to run code and reproduce experiments.

In the Machine Learning Operations (MLOps) community these automation tools are often called [task or workflow orchestration](https://www.datarevenue.com/en-blog/airflow-vs-luigi-vs-argo-vs-mlflow-vs-kubeflow). There are many options, such as [Airflow](https://airflow.apache.org/), [Luigi](https://github.com/spotify/luigi), [MLflow](https://mlflow.org/), [Kubeflow](https://www.kubeflow.org/) and [iterative.ai's DVC and CML](https://iterative.ai/), all with various additional features for versioning experiments, scheduling and visualizations, but at the core they are all built on the same dependency graph principle as the OG [Make](https://opensource.com/article/18/8/what-how-makefile).

Some of these tools can take a lot of work to set up, so discuss the trade-offs with your team to decide what you'd like to use. In the early stages of a project, we recommend using something easy to set up, like [DVC](https://dvc.org/) or [Make](https://opensource.com/article/18/8/what-how-makefile).

### DVC Example
In this repository, we have set up a pipeline using [DVC](https://dvc.org/), which has the added benefit of versioning data and experiments. DVC is especially easy to set up for Python projects, because it can be installed via pip in the project requirements and integrates with git. See [DVC Get Started documentation](https://dvc.org/doc/start) for instructions on setting up DVC in your own repository.

The stages in our word count experiment pipeline are configured in `dvc.yaml`. As described in the previous section, this takes the `data/gutenberg` files as input and produces `data/gutenberg_counts.csv` as the final product. Since `data/gutenberg_counts.csv` should be generated whenever the data or scripts change, it is managed by DVC and ignored by git. You can re-run the pipeline steps by running `dvc repro`.
```
$ dvc repro
Running stage 'count-words':
> python cdstemplate/corpus_counter_script.py data/gutenberg_counts.csv data/gutenberg/*.txt --case-insensitive
INFO : 2022-05-23 11:18:42,813 : __main__ : Command line arguments: Namespace(csv='data/gutenberg_counts.csv', documents=['data/gutenberg/austen-emma.txt', 'data/gutenberg/austen-persuasion.txt', 'data/gutenberg/austen-sense.txt', 'data/gutenberg/bible-kjv.txt', 'data/gutenberg/blake-poems.txt', 'data/gutenberg/bryant-stories.txt', 'data/gutenberg/burgess-busterbrown.txt', 'data/gutenberg/carroll-alice.txt', 'data/gutenberg/chesterton-ball.txt', 'data/gutenberg/chesterton-brown.txt', 'data/gutenberg/chesterton-thursday.txt'], case_insensitive=True)
...
$ dvc repro
Stage 'count-words' didn't change, skipping
Data and pipelines are up to date.
```


You can see the stages in the DAG by running `dvc dag`, in our case it's just a single step called `count-words`:
```
$ dvc dag
+-------------+
| count-words |
+-------------+
```

## A Note on Notebooks
We have also included an example Jupyter notebook

Jupyter notebooks are useful tools for exploratory data analysis, prototyping baseline models and creating visualizations. However, they are _not_ an acceptable way to hand-off code for others to reproduce. Have you ever tried to run someone else's notebook, only to find out a cell was deleted, and you have no idea what it was supposed to do?

[Don't put data science notebooks into production](https://martinfowler.com/articles/productize-data-sci-notebooks.html), they are [hard to test, version, parametrize and keep track of state](https://www.reddit.com/r/datascience/comments/ezh50g/jupyter_notebooks_in_productionno_just_no/).

There _are_ [companies that use notebooks in production architecture](https://blog.goodaudience.com/inside-netflixs-notebook-driven-architecture-aedded32145e), but they have entire Devops organizations to help configure deployment and _still_ use workflow tools like [papermill](https://papermill.readthedocs.io/en/latest/) and Airflow to parametrize notebook dependencies. Unless you are willing to put in the effort to parametrize your notebooks in pipeline workflows, don't use them when stability and reproducibility matter.

Best practices for working with notebooks are changing as they become more popular. However, for now most of these services are too expensive for our partners or difficult to configure. You can use a notebook for prototyping and exploratory analysis, but once the project moves forward, use [`nbconvert`](https://linuxhint.com/convert-jupyter-notebook-python/) to convert the notebook to python code, then add some tests!
