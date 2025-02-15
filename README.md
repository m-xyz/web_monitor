# Website Availability Monitor
=====================================

## Overview
------------

Monitor website availability using Selenium.

## Features
------------

* Uses Selenium WebDriver to simulate a browser visit
* Logs results to a file
* Configurable via a XML file

## Requirements
---------------

* Python 3.8+
* Selenium WebDriver
* Firefox, Chrome or Edge browser

## Installation
------------

1. Clone the repository: `git clone https://github.com/m-xyz/web_monitor.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Adjust the configuration file if needed: `params.xml`

## Usage
-----

1. Run the monitor: `python main.py -b <BROWSER>`, if no browser is provided defaults to Chrome
2. View the execution logs: `logs/website_availability.log`
3. If an error occurs a directory will be created `logs/<CURRENT_DATE>`, which contains an error log and a screenshot of the website at the time of failure.
