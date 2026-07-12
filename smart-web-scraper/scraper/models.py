"""Data model shared by the scraper, parser and exporter modules."""
from dataclasses import dataclass, asdict


@dataclass
class Product:
    name: str
    price: str
    rating: str
    product_url: str
    image_url: str
    availability: str
    category: str

    def to_dict(self) -> dict:
        return asdict(self)
