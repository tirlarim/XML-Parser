# Python XML Downloader and Parser

This Python program downloads an XML file, parses it to extract important information, saves the extracted information into a PostgreSQL database, and downloads music from a link provided in the XML file to a specified directory on the PC.

Features

	•	Downloads XML file from a given URL.
	•	Parses the XML file to extract important information.
	•	Saves the parsed information into a PostgreSQL database.
	•	Downloads audio files from links in the XML and saves them to a specified directory.

Prerequisites

Before you can run this program, ensure you have the dependencies listed in [requirements.txt](requirements.txt) installed:

`pip install -r requirements.txt`

## Setup

Ensure you have PostgreSQL installed and running. You also need to create a database where the extracted XML information will be stored.
After it, you need to add you personal PG_HOST_DEBUG, PG_PORT_DEBUG, PG_NAME_DEBUG, and PG_LOGIN_DEBUG to [.env](.env)


## Usage

python ./main.py

## License

This project is licensed under the MIT License.
