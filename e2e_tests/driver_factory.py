import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def create_driver(options):
    """Create a webdriver instance.

    If `SELENIUM_REMOTE_URL` is set in the environment, create a Remote WebDriver
    pointing to that URL (useful for CI with selenium/standalone-chrome service).
    Otherwise install a chromedriver with webdriver-manager and start a local Chrome.
    """
    remote = os.environ.get('SELENIUM_REMOTE_URL')
    if remote:
        return webdriver.Remote(command_executor=remote, options=options)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
