from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Inventory:
    id: Optional[str] = None
    shop_id: str = ""
    product_id: str = ""
    current_stock: int = 0
    selling_price: float = 0.0
    cost_price: float = 0.0
    reorder_level: int = 5  # Low stock alert threshold
    last_updated: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self):
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'product_id': self.product_id,
            'current_stock': self.current_stock,
            'selling_price': self.selling_price,
            'cost_price': self.cost_price,
            'reorder_level': self.reorder_level,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data):
        inventory = cls()
        inventory.id = data.get('id')
        inventory.shop_id = data.get('shop_id', '')
        inventory.product_id = data.get('product_id', '')
        inventory.current_stock = data.get('current_stock', 0)
        inventory.selling_price = data.get('selling_price', 0.0)
        inventory.cost_price = data.get('cost_price', 0.0)
        inventory.reorder_level = data.get('reorder_level', 5)
        inventory.is_active = data.get('is_active', True)
        
        if data.get('last_updated'):
            inventory.last_updated = datetime.fromisoformat(data['last_updated'])
        
        return inventory
