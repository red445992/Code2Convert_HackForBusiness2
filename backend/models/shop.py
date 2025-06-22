from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Shop:
    id: Optional[str] = None
    name: str = ""
    owner_name: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    district: str = ""
    registration_date: Optional[datetime] = None
    is_active: bool = True
    subscription_tier: str = "free"  # free, basic, premium

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner_name': self.owner_name,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'district': self.district,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier
        }

    @classmethod
    def from_dict(cls, data):
        shop = cls()
        shop.id = data.get('id')
        shop.name = data.get('name', '')
        shop.owner_name = data.get('owner_name', '')
        shop.phone = data.get('phone', '')
        shop.address = data.get('address', '')
        shop.city = data.get('city', '')
        shop.district = data.get('district', '')
        shop.is_active = data.get('is_active', True)
        shop.subscription_tier = data.get('subscription_tier', 'free')
        
        if data.get('registration_date'):
            shop.registration_date = datetime.fromisoformat(data['registration_date'])
        
        return shop