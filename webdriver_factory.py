from abc import ABC, abstractmethod

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWD


class WebDriverAbstractFactory(ABC):
    """An abstract factory for webdrivers."""
    @abstractmethod
    def create_driver(self):
        pass


class ChromeWebDriverFactory(WebDriverAbstractFactory):
    def create_driver(self) -> ChromeWD:
        chrome_options = Options()
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument(
            'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"'
        )
        return webdriver.Chrome(options=chrome_options)
