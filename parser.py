import pandas as pd
from pydantic import ValidationError

from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from dataclass import Product
from webdriver_factory import WebDriverAbstractFactory, ChromeWebDriverFactory


class Parser:
    filename = settings.excel_filename
    articles_number = settings.articles_number
    link_to_parse = settings.link_to_parse

    def __init__(self, driver_factory: WebDriverAbstractFactory):
        self.driver_factory = driver_factory
    
    def main(self, page_link: str) -> None:
        with self.driver_factory.create_driver() as driver:
            driver.get(page_link)
            while Parser._captcha_found(driver):
                input("Пройдите CAPTCHA вручную и нажмите Enter.")
                cookies = driver.get_cookies()
                for cookie in cookies:
                    driver.add_cookie(cookie)
            if Parser._region_checker_found(driver):
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'close-button'))
                ).click()
            try:
                product_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR,
                        '''a[data-test="product-name-link"],
                        a.catalog-item-regular-desktop__title-link.ddl_product_link'''
                    ))
                )
            except TimeoutException:
                print('Не удалось загрузить элементы продуктов на странице.')
                return
            if product_elements:
                try:
                    links = Parser._get_links(product_elements)
                    products: Product = Parser._extract(links, driver)
                    Parser._save_to_excel(products, Parser.filename)
                except Exception as e:
                    print(f'Ошибка при извлечении данных или сохранении в Excel: {e}')
                    return
    
    @staticmethod
    def _captcha_found(driver: WebDriver) -> bool:
        # Проверить наличие CAPTCHA.
        try:
            captcha_element = driver.find_element(By.ID, 'captcha-holder')
            return captcha_element.is_displayed()
        except NoSuchElementException:
            return False
        
    @staticmethod
    def _region_checker_found(driver: WebDriver) -> bool:
        # Проверить наличие блокирующего окна "Ваш регион".
        try:
            region_checker = driver.find_element(
                By.CLASS_NAME, 'header-region-selector-view__title'
            )
            return region_checker.is_displayed()
        except NoSuchElementException:
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
    def _extract(links: list[str], driver: WebDriver) -> list[Product]:
        # Извлечь данные из найденных веб-элементов.
        products = []
        for link in links:
            try:
                driver.get(link)
                while Parser._captcha_found(driver):
                    input("Пройдите CAPTCHA вручную и нажмите Enter.")
                    cookies = driver.get_cookies()
                    if cookies:
                        for cookie in cookies:
                            driver.add_cookie(cookie)
                name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 'h1[itemprop="name"]'
                    ))
                ).text
                price = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        'span.sales-block-offer-price__price-final'
                    ))
                ).text
                try:
                    description = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            'div[itemprop="description"].text-block'
                        ))
                    ).text
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
                print(f'''Произошла ошибка при парсинге страницы: {e}. '''
                      '''Извлечено товаров: {len(products)}.''')
                return products
            except Exception as e:
                print(f'''Произошла непредвиденная ошибка при парсинге страницы: {e}. '''
                      '''Извлечено товаров: {len(products)}.''')
                return products
        return products
    
    @staticmethod
    def _get_links(elements: list[WebElement]) -> list[str]:
        # Получить ссылки на товары из найденных веб-элементов.
        filtered_links = [
            element.get_attribute('href') for element in elements \
                if 'promo' not in element.get_attribute('href').lower()
        ]
        return filtered_links[:Parser.articles_number]  # Первые 20 ссылок

    @staticmethod
    def _save_to_excel(products: list[Product], filename: str) -> None:
        # Сохранить извлеченные данные в таблицу Excel.
        try:
            df = pd.DataFrame([product.__dict__ for product in products])
            df['description'] = df['description'].fillna("")
            df = df.rename(columns={
                'price': 'RUB Price',
                'link': 'Product URL',
                'description': 'Description',
                'name': 'Name',
            })
            # Расставляем поля в нужном порядке
            df = df[['Product URL', 'Name', 'RUB Price', 'Description']]
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=filename.split('.')[0], index=False)
        except Exception as e:
            print(f'Ошибка при сохранении данных в Excel: {e}')


if __name__ == '__main__':
    webdriver_factory = ChromeWebDriverFactory()
    extractor = Parser(webdriver_factory)
    extractor.main(Parser.link_to_parse)
