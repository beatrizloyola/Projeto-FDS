import os
import socket
import time
import urllib.parse
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
            """Proxy WebDriver that retries URL loads with host rewrites.

            Behavior:
            - Try the original URL first.
            - On known network errors (connection refused / name not resolved),
              attempt a sequence of rewrites and retry each one.
            - The sequence uses an optional env var `SELENIUM_HOST_REWRITE` (can
              be an IP or hostname), then `host.docker.internal`, then
              `172.17.0.1` (common Docker gateway). This makes CI more robust
              across runners and Docker setups.
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
                    known = (
                        'ERR_CONNECTION_REFUSED', 'ERR_NAME_NOT_RESOLVED',
                        'net::ERR_CONNECTION_REFUSED', 'net::ERR_NAME_NOT_RESOLVED'
                    )
                    if not any(token in msg for token in known):
                        raise

                    parsed = urllib.parse.urlparse(url)
                    netloc = parsed.netloc
                    host_part = netloc.split(':')[0] if netloc else ''
                    port_part = netloc.split(':')[1] if ':' in netloc else ''

                    candidates = []
                    env_host = os.environ.get('SELENIUM_HOST_REWRITE')
                    if env_host:
                        candidates.append(env_host)

                    candidates.extend([
                        'host.docker.internal',
                        '127.0.0.1',
                        'localhost',
                        '172.17.0.1',
                    ])

                    try:
                        host_ip = socket.gethostbyname(socket.gethostname())
                        if host_ip and host_ip not in candidates:
                            candidates.append(host_ip)
                    except Exception:
                        pass

                    last_exc = exc
                    for host in candidates:
                        if not host:
                            continue
                        new_netloc = host + (':' + port_part if port_part else '')
                        rewritten = urllib.parse.urlunparse(parsed._replace(netloc=new_netloc))
                        try:
                            print(f"[e2e] host rewrite attempt: {url} -> {rewritten}")
                            time.sleep(0.3)
                            return self._driver.get(rewritten)
                        except _selenium_exceptions.WebDriverException as exc2:
                            last_exc = exc2
                            continue

                    raise last_exc

            def __getattr__(self, name):
                return getattr(self._driver, name)

        return HostRewriteWebDriver(remote_driver)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
