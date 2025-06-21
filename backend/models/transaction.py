
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Transaction:
    id: Optional[str] = None
    shop_id: str = ""
    product_id: str = ""
    transaction_type: str = ""  # sale, restock, adjustment
    quantity: int = 0
    price_per_unit: float = 0.0
    total_amount: float = 0.0
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None
    created_by: str = "system"

    def to_dict(self):
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'product_id': self.product_id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price_per_unit': self.price_per_unit,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'created_by': self.created_by
        }

    @classmethod
    def from_dict(cls, data):
        transaction = cls()
        transaction.id = data.get('id')
        transaction.shop_id = data.get('shop_id', '')
        transaction.product_id = data.get('product_id', '')
        transaction.transaction_type = data.get('transaction_type', '')
        transaction.quantity = data.get('quantity', 0)
        transaction.price_per_unit = data.get('price_per_unit', 0.0)
        transaction.total_amount = data.get('total_amount', 0.0)
        transaction.notes = data.get('notes')
        transaction.created_by = data.get('created_by', 'system')
        
        if data.get('transaction_date'):
            transaction.transaction_date = datetime.fromisoformat(data['transaction_date'])
        
        return transaction