from decimal import Decimal
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    delivery_address: Dict[str, Any]
    delivery_slot: str = "15 Minutes Express"
    payment_method: str = "card"
    coupon_code: Optional[str] = None

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    product_name: str
    product_image: str
    unit: str
    price: Decimal
    quantity: int
    total_price: Decimal

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    status: str
    subtotal: Decimal
    discount: Decimal
    delivery_fee: Decimal
    tax: Decimal
    total: Decimal
    delivery_address: Dict[str, Any]
    delivery_slot: str
    payment_method: str
    payment_status: str
    created_at: datetime
    items: List[OrderItemResponse] = Field(default_factory=list)
