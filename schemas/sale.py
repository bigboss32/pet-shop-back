from pydantic import BaseModel, EmailStr, condecimal
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from .user import UserSimple

# =========================
# ITEMS
# =========================

class SaleItemBase(BaseModel):
    product_id: int
    quantity: condecimal(gt=0, max_digits=10, decimal_places=3)
    price: condecimal(gt=0, max_digits=10, decimal_places=2)


class SaleItemResponse(SaleItemBase):
    id: int
    subtotal: condecimal(max_digits=10, decimal_places=2)
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


# =========================
# SALE
# =========================

class SaleBase(BaseModel):
    payment_method: str
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    discount: condecimal(ge=0, max_digits=10, decimal_places=2) = Decimal("0")
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    items: List[SaleItemBase]


class SaleResponse(SaleBase):
    id: int
    total: condecimal(max_digits=10, decimal_places=2)
    subtotal: condecimal(max_digits=10, decimal_places=2)
    tax: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime
    user: Optional[UserSimple] = None
    items: List[SaleItemResponse]

    class Config:
        from_attributes = True


class SaleWithUserResponse(SaleResponse):
    user: Optional[UserSimple] = None

    class Config:
        from_attributes = True
