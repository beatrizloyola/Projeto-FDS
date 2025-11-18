import os
from selenium import webdriver
from selenium.common import exceptions as _selenium_exceptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os as _os


def create_driver(options):
    """Create a webdriver instance.

    If `SELENIUM_REMOTE_URL` is set in the environment, create a Remote WebDriver
    pointing to that URL (useful for CI with selenium/standalone-chrome service).
    Otherwise install a chromedriver with webdriver-manager and start a local Chrome.
    """
    remote = os.environ.get('SELENIUM_REMOTE_URL')
    if remote:
        remote_driver = webdriver.Remote(command_executor=remote, options=options)

        class HostRewriteWebDriver:
            """Proxy WebDriver that rewrites localhost URLs to host.docker.internal.

            It forwards all attribute access to the underlying driver but overrides
            `get()` to rewrite the target host when running against a remote
            Selenium service (CI).
            """

            def __init__(self, driver):
                self._driver = driver

            def get(self, url):
                if url is None:
                    return self._driver.get(url)
                try:
                    return self._driver.get(url)
                except _selenium_exceptions.WebDriverException as exc:
                    msg = str(exc)
                    if 'ERR_CONNECTION_REFUSED' in msg or 'ERR_NAME_NOT_RESOLVED' in msg or 'net::ERR_CONNECTION_REFUSED' in msg or 'net::ERR_NAME_NOT_RESOLVED' in msg:
                        rewritten = url.replace('localhost', 'host.docker.internal').replace('127.0.0.1', 'host.docker.internal')
                        return self._driver.get(rewritten)
                    raise

            def __getattr__(self, name):
                return getattr(self._driver, name)

        return HostRewriteWebDriver(remote_driver)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
