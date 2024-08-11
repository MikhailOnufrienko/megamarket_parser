from pydantic import Field
from pydantic_settings import BaseSettings


class ParserConfig(BaseSettings):
    articles_number: int = Field(
        default=20, description='Количество товаров для извлечения'
    )
    excel_filename: str = Field(
        default='goods.xlsx', description='Название файла Excel'
    )

settings = ParserConfig()
