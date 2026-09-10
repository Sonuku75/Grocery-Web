from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductResponse

class CartItemBase(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1)

class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    quantity: int
    product: ProductResponse

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    items: List[CartItemResponse]
    item_count: int
    subtotal: Decimal
    discount: Decimal
    delivery_fee: Decimal
    tax: Decimal
    total: Decimal
