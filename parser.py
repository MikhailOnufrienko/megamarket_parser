import time

import pandas as pd
from pydantic import ValidationError

from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from dataclass import Product
from webdriver_factory import WebDriverAbstractFactory, ChromeWebDriverFactory    


class Parser:
    def __init__(self, driver_factory: WebDriverAbstractFactory):
        self.driver_factory = driver_factory
    
    def main(self, page_link: str) -> None:
        with self.driver_factory.create_driver() as driver:
            driver.get(page_link)
            if Parser._is_captcha_present(driver):
                input("Пройдите CAPTCHA вручную и нажмите Enter.")
                cookies = driver.get_cookies()
                for cookie in cookies:
                    driver.add_cookie(cookie)
            time.sleep(2)
            try:
                product_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-test="product-name-link"]'))
                )
            except TimeoutException:
                print('Не удалось загрузить элементы продуктов на странице.')
                return
            if product_elements:
                try:
                    products: Product = Parser._extract(product_elements[:1], driver)
                    Parser._save_to_excel(products)
                except Exception as e:
                    print(f'Ошибка при извлечении данных или сохранении в Excel: {e}')
    
    @staticmethod
    def _is_captcha_present(driver: WebDriver) -> bool:
        # Проверить наличие CAPTCHA.
        try:
            captcha_element = driver.find_element(By.ID, 'captcha-holder')
            return captcha_element.is_displayed()
        except NoSuchElementException as e:
            return False
    
    @staticmethod
    def _price_to_float(price: str) -> float:
        # Преобразовать строкое представление цены в тип float.
        try:
            price_cleaned = price.replace(" ", "").replace("₽", "")
            return round(float(price_cleaned), 2)
        except ValueError:
            print(f'Не удалось преобразовать цену "{price}" в тип float.')
            return 0.00
    
    @staticmethod
    def _extract(elements: list[WebElement], driver: WebDriver) -> list[Product]:
        # Извлечь данные из найденных веб-элементов.
        products = []
        for element in elements:
            try:
                link = element.get_attribute('href')
                driver.get(link)
                time.sleep(2)
                name=driver.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text
                price=driver.find_element(By.CSS_SELECTOR, 'span.sales-block-offer-price__price-final').text
                try:
                    description=driver.find_element(By.CSS_SELECTOR, 'div[itemprop="description"].text-block').text
                except NoSuchElementException:
                    continue
                try:
                    product = Product(
                        name=name,
                        link=link,
                        price=Parser._price_to_float(price),
                        description=description,
                    )
                    products.append(product)
                except ValidationError as e:
                    print(f'Не удалось создать объект Product: {e}')
                    continue
            except WebDriverException as e:
                print(f'Произошла ошибка при парсинге страницы: {e}')
                return []
            except Exception as e:
                print(f'Произошла непредвиденная ошибка при парсинге страницы: {e}')
                return []
        return products

    @staticmethod
    def _save_to_excel(products: list[Product], filename='goods.xlsx') -> None:
        # Сохранить извлеченные данные в таблицу Excel.
        try:
            df = pd.DataFrame([product.__dict__ for product in products])
            df['description'] = df['description'].fillna("")
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='goods', index=False)
        except Exception as e:
            print(f'Ошибка при сохранении данных в Excel: {e}')


if __name__ == '__main__':
    webdriver_factory = ChromeWebDriverFactory()
    extractor = Parser(webdriver_factory)
    extractor.main(r'https://megamarket.ru/catalog/?q=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%BE%D0%B5%20%D0%BA%D1%80%D0%B5%D1%81%D0%BB%D0%BE')
