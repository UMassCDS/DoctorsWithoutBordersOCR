# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

You should also add project tags for each release in Github, see [Managing releases in a repository](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## [Unreleased]

## [2.0.0] - 2024-08-13
### Added
- Merged the MSF-OCR-Streamlit repository into this repository
- User authenticates with DHIS2 password rather than hard coded passkey
- Table headers are corrected based on key-value pairs from DHIS2
- Payload with key-value pairs for DHIS2 is displayed to the user before uploading
- Images are resized before being sent to OpenAI 
- Added all UI features such as DHIS2 authentication, multiple tally sheet processing, left bar on streamlit, buttons present in 
LLM version of app into docTR version. 

### Changed
- User must confirm each page and key-value pairs before they're allowed to upload, so upload buttons is not initially selectable

### Fixed
- Bug where a user's changes aren't saved every other time or when confirming in the Streamlit app

## [1.1.0] - 2024-07-26
### Changed
- Requests to OpenAI are multithreaded to speed up time to get results for multiple images

## [1.0.0] - 2024-07-19
### Added
- More comprehensive querying in DHIS2 for organization and dataset names
- Added OpenAI backed OCR functionality

### Changed
- Module names changed to meet PEP 8 naming conventions
- Server settings and API keys set via environment variables instead of settings file

## [0.0.1] - 2024-07-03
### Added
- Notebook for downloading sample test data
- msfocr.data.data_upload_DHIS2 created for sending key/value pairs to a DHIS2 server
- msfocr.docTR created to implement extracting tables from images using image2table and docTR
- Initial package structure created
