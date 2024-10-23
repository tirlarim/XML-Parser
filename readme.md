# Python XML Downloader and Parser

This Python program downloads an XML file, parses it to extract important information, saves the extracted information into a PostgreSQL database, and downloads music from a link provided in the XML file to a specified directory on the PC.

Features

	•	Downloads XML file from a given URL.
	•	Parses the XML file to extract important information.
	•	Saves the parsed information into a PostgreSQL database.
	•	Downloads audio files from links in the XML and saves them to a specified directory.

Prerequisites

Before you can run this program, ensure you that you set up environment and have the dependencies listed in [requirements.txt](requirements.txt) installed:

```bash
python3 -m venv .venv
pip install -r requirements.txt
```

## Setup

Ensure you have PostgreSQL installed and running. You also need to create a database where the extracted XML information will be stored.
After it, you need to add you personal PG_HOST_DEBUG, PG_PORT_DEBUG, PG_NAME_DEBUG, and PG_LOGIN_DEBUG to [.env](.env)

### Dotenv file example
PG_DEBUG="1" # set 0 to connect to main bd, set 1 to connect to DEBUG bd\
PG_HOST="abc.com"\
PG_PORT="1234"\
PG_LOGIN="Ivan_Ivanov"\
PG_PASS="Ivanovich_1994"\
PG_HOST_DEBUG="localhost"\
PG_PORT_DEBUG="5432"\
PG_NAME_DEBUG="local_Ivanovich_1994"\
PG_LOGIN_DEBUG="Ivan_Ivanov_home_PC"


## Usage

`python -m src.main`

## License

This project is licensed under the MIT License.
