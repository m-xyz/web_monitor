import os
import time
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
import xml.etree.ElementTree as ET


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
LOG_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_driver(browser="chrome"):
    """
    Sets up a WebDriver instance for the specified browser.

    :param browser: the name of the browser to use (chrome, edge, or firefox)
    :return: the WebDriver instance
    :raises ValueError: if the specified browser is not supported
    """
    if browser == "chrome":
        options = ChromeOptions()
        driver_path = params["chrome_driver_path"]
        service = ChromeService(driver_path)
        return webdriver.Chrome(service=service, options=options)
    elif browser == "edge":
        options = EdgeOptions()
        driver_path = params["edge_driver_path"]
        service = EdgeService(driver_path)
        return webdriver.Edge(service=service, options=options)
    elif browser == "firefox":
        options = FirefoxOptions()
        driver_path = params["firefox_driver_path"]
        service = FirefoxService(driver_path)
        return webdriver.Firefox(service=service, options=options)
    else:
        raise ValueError("Unsupported browser!")

def monitor_website(browser="chrome"):
    """
    Monitors the availability of a website on a specified browser (defaults to Chrome).

    :param browser: the name of the browser to use (chrome, edge, or firefox)
    """
    try:
        # Initialize WebDriver for the specified browser
        #driver = setup_driver(browser)
        driver = webdriver.Firefox()
        driver.maximize_window()

        # [1] Access website
        driver.get(params["website_url"])
        driver_wait = WebDriverWait(driver, params["event_wait"])

        time.sleep(3)

        # [2] Handle consent popup
        driver_wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="consent_prompt_submit"]'))).click()

        # [3] Scroll down and click "Find an agency"
        driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//p[text()='Trouver une agence']/ancestor::span[@class='link-list lnk']"
                )
            )
        ).click()

        # [4] Fill the form and search
        driver.find_element(By.ID, "em-search-form__searchstreet").send_keys(f"{params["agency_name"]}\n")
        driver.find_element(By.ID, "em-search-form__searchcity").send_keys(f"{params["agency_postal_code"]}\n")

        time.sleep(3)

        driver_wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    ".em-search-form__submit.em-button.em-button--primary"
                )
            )
        ).click()

        time.sleep(3)

        # [5] Click on location 4 on the map
        # TODO: Implement this

    except Exception as e:
        print(f"[ERROR] {e}")
        log_path = os.path.join("logs", LOG_DATE)
        os.makedirs(log_path, exist_ok=True)
        screenshot_path = os.path.join(log_path, f"error_screenshot_{browser}.png")
        driver.save_screenshot(screenshot_path)

    finally: driver.quit()

if __name__ == "__main__":
    monitor_website("firefox")
