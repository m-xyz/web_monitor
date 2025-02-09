import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import xml.etree.ElementTree as ET
import argparse

LOG_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and a stream handler
file_handler = logging.FileHandler(f'logs/{LOG_DATE}_web_monitor.log')
stream_handler = logging.StreamHandler()

# Create a formatter and add it to the handlers
formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def load_params(file_path):
    """
    Loads parameters from an XML file into a dictionary.

    :param file_path: the path to the XML file
    :return: a dictionary of parameters
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    return {child.tag: child.text for child in root}

params = load_params("params.xml")

def setup_driver(browser="chrome"):
    """
    Sets up a WebDriver instance for the specified browser.

    :param browser: the name of the browser to use (chrome, edge, or firefox)
    :return: the WebDriver instance
    :raises ValueError: if the specified browser is not supported
    """
    if browser == "chrome":
        options = ChromeOptions()
        #driver_path = params["chrome_driver_path"]
        #service = ChromeService(driver_path)
        #return webdriver.Chrome(service=service, options=options)
        return webdriver.Chrome(options=options)
    elif browser == "edge":
        options = EdgeOptions()
        #driver_path = params["edge_driver_path"]
        #service = EdgeService(driver_path)
        #return webdriver.Edge(service=service, options=options)
        return webdriver.Edge(options=options)
    elif browser == "firefox":
        options = FirefoxOptions()
        #driver_path = params["firefox_driver_path"]
        #service = FirefoxService(driver_path)
        #return webdriver.Firefox(service=service, options=options)
        return webdriver.Firefox(options=options)
    else:
        raise ValueError("Unsupported browser!")

def monitor_website(browser):
    """
    Monitors the availability of a website on a specified browser (defaults to Chrome).

    :param browser: the name of the browser to use (chrome, edge, or firefox)
    """
    try:
        # Initialize WebDriver for the specified browser
        driver = setup_driver(browser)
        driver.maximize_window()

        # [1] Access website
        logger.info(f"Browser: {browser}")
        logger.info(f'Accessing URL \'{params["website_url"]}\'')
        driver.get(params["website_url"])
        driver_wait = WebDriverWait(driver, params["event_wait"])
        logger.info(f'Successfully accessed \'{params["website_url"]}\'')

        # [2] Handle consent popup
        driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//*[@id="consent_prompt_submit"]',
                ),
            ),
        ).click()
        logger.info("Cookies popup clicked.")

        # [3] Scroll down and click "Find an agency"
        driver_wait.until(
            EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//p[text()='Trouver une agence']/ancestor::span[@class='link-list lnk']",
                    ),
            ),
        ).click()
        logger.info("Find agency button clicked.")

        # [4] Fill the form and search

        # Fill in the first text box
        driver.find_element(
            By.ID,
            "em-search-form__searchstreet",
        ).send_keys(params["agency_name"])

        # Wait until the first text box contains the expected value
        WebDriverWait(driver, 10).until(
            lambda driver: driver.find_element(
                By.ID,
                "em-search-form__searchstreet",
            ).get_attribute("value") == params["agency_name"]
        )
        logger.info(f"Searching agency \'{params['agency_name']}\'...")

        # Fill in the second text box
        driver.find_element(
            By.ID,
            "em-search-form__searchcity"
        ).send_keys(params["agency_postal_code"])

        # Wait until the second text box contains the expected value
        WebDriverWait(driver, 10).until(
            lambda driver: driver.find_element(
                By.ID,
                "em-search-form__searchcity",
            ).get_attribute("value") == params["agency_postal_code"]
        )
        logger.info(f"Searching agency postal code \'{params['agency_postal_code']}\'...")

        # Wait for the search button to be clickable and click it
        driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    ".em-search-form__submit.em-button.em-button--primary",
                ),
            ),
        ).click()

        # [5] Click on location 4 on the map
        agency_waypoint = driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f'//div[@id="searchmap"]//td[text()="{params["agency_number"]}"]',
                ),
            ),
        )
        ActionChains(driver).double_click(agency_waypoint).perform()
        logger.info(f"Agency \'{params["agency_name"]}\' @ {params['agency_postal_code']} found.")
        
        time.sleep(2)

        logger.info(f"\'{params["website_url"]}\' is up and running.")

    except Exception as e:
        logger.error(f"{e}")
        log_path = os.path.join("logs", LOG_DATE)
        os.makedirs(log_path, exist_ok=True)
        screenshot_path = os.path.join(log_path, f"error_screenshot_{browser}.png")
        driver.save_screenshot(screenshot_path)

    finally: driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor website availability.")
    parser.add_argument(
        "-b",
        "--browser",
        type=str.lower,
        choices=["chrome", "edge", "firefox"],
        default="chrome",
        help="Select browser to run (default: chrome)",
    )
    args = parser.parse_args()
    monitor_website(args.browser)