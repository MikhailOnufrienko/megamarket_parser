from typing import Optional

from pydantic import Field, ValidationError, HttpUrl
from pydantic.dataclasses import dataclass


@dataclass
class Product:
    price: float
    link: HttpUrl
    description: Optional[str]
    name: str = Field(..., min_length=2)
