from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Product:
    id: Optional[str] = None
    name: str = ""
    category: str = ""
    brand: str = ""
    unit: str = "piece"  # piece, kg, liter, packet
    barcode: Optional[str] = None
    default_price: float = 0.0
    image_url: Optional[str] = None
    is_common: bool = False  # Pre-loaded common products
    created_date: Optional[datetime] = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'brand': self.brand,
            'unit': self.unit,
            'barcode': self.barcode,
            'default_price': self.default_price,
            'image_url': self.image_url,
            'is_common': self.is_common,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

    @classmethod
    def from_dict(cls, data):
        product = cls()
        product.id = data.get('id')
        product.name = data.get('name', '')
        product.category = data.get('category', '')
        product.brand = data.get('brand', '')
        product.unit = data.get('unit', 'piece')
        product.barcode = data.get('barcode')
        product.default_price = data.get('default_price', 0.0)
        product.image_url = data.get('image_url')
        product.is_common = data.get('is_common', False)
        
        if data.get('created_date'):
            product.created_date = datetime.fromisoformat(data['created_date'])
        
        return product
