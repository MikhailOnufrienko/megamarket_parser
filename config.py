from pydantic import Field
from pydantic_settings import BaseSettings


class ParserConfig(BaseSettings):
    articles_number: int = Field(
        default=20, description='Количество товаров для извлечения',
    )
    excel_filename: str = Field(
        default='goods.xlsx', description='Название файла Excel',
    )
    link_to_parse: str = Field(
        default='https://megamarket.ru/catalog/?q=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%BE%D0%B5%20%D0%BA%D1%80%D0%B5%D1%81%D0%BB%D0%BE',
        description='Ссылка для парсинга',
    )

settings = ParserConfig()
