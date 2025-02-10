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

LOG_DATE = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LOG_DIR = "logs"
log_execution = f'{LOG_DATE}_web_monitor.log'
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, log_execution)
file_handler = logging.FileHandler(log_path)
stream_handler = logging.StreamHandler()

formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def load_params(file_path):
    """
    Loads parameters from an XML file into a dictionary.

    :param file_path: the path to the XML file
    :return: a dictionary of parameters
    """
    #tree = ET.parse(file_path)
    root = ET.parse(file_path).getroot()
    return {child.tag: child.text for child in root}

params = load_params("params.xml")

def setup_driver(browser="chrome"):
    """
    Sets up a WebDriver instance for the specified browser.

    :param browser: the name of the browser to use (chrome, edge, or firefox)
    :return: the WebDriver instance
    :raises ValueError: if the specified browser is not supported
    """
    if browser == "chrome": return webdriver.Chrome(options=ChromeOptions())
    elif browser == "edge": return webdriver.Edge(options=EdgeOptions())
    elif browser == "firefox": return webdriver.Firefox(options=FirefoxOptions())
    else: raise ValueError("Unsupported browser!")

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
        logger.info(f'Browser: {browser}')
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
                        '//p[text()="Trouver une agence"]/ancestor::span[@class="link-list lnk"]',
                    ),
            ),
        ).click()
        logger.info("Find agency button clicked.")

        # [4] Fill the form and search

        driver.find_element(
            By.ID,
            'em-search-form__searchstreet',
        ).send_keys(params["agency_name"])

        driver_wait.until(
            lambda driver: driver.find_element(
                By.ID,
                'em-search-form__searchstreet',
            ).get_attribute("value") == params["agency_name"]
        ); logger.info(f'Searching agency \'{params["agency_name"]}\'...')

        driver.find_element(
            By.ID,
            'em-search-form__searchcity'
        ).send_keys(params["agency_postal_code"])

        driver_wait.until(
            lambda driver: driver.find_element(
                By.ID,
                'em-search-form__searchcity',
            ).get_attribute("value") == params["agency_postal_code"]
        ); logger.info(f'Searching agency postal code \'{params["agency_postal_code"]}\'...')

        # Search
        driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    '.em-search-form__submit.em-button.em-button--primary',
                ),
            ),
        ).click()

        time.sleep(5)
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
        logger.info(f'Agency \'{params["agency_name"]}\' @ {params["agency_postal_code"]} found.')
        
        time.sleep(2)

        logger.info(f'\'{params["website_url"]}\' is up and running.')

    except Exception as e:
        logger.error(f'{e}')

        error_dir = os.path.join(LOG_DIR, f'error_{LOG_DATE}')
        os.makedirs(error_dir, exist_ok=True)
        screenshot_path = os.path.join(error_dir, f'error_screenshot_{browser}.png')
        
        try:
            driver.save_screenshot(screenshot_path)

            logger.info(f'Screenshot saved at: {screenshot_path}')
            
            error_log_path = os.path.join(error_dir, f'execution_log_{browser}.log')
            with open(log_path, 'r') as original_log:
                with open(error_log_path, 'w') as error_log:
                    error_log.write(original_log.read())
            
            logger.info(f"Execution log saved at: {error_log_path}")
        
        except Exception as screenshot_error:
            logger.error(f"Failed to save screenshot or execution log: {screenshot_error}")

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