from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=128)
    brand: str = Field(..., max_length=128)
    category_id: str
    description: str
    specifications: Dict[str, Any] = Field(default_factory=dict)
    price: Decimal = Field(..., ge=0)
    original_price: Decimal = Field(..., ge=0)
    discount_percent: int = Field(0, ge=0, le=100)
    unit: str = "1 unit"
    stock: int = Field(0, ge=0)
    rating: Decimal = Field(Decimal("5.0"), ge=0, le=5)
    rating_count: int = Field(0, ge=0)
    images: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_popular: bool = False
    is_featured: bool = False
    is_deal: bool = False
    in_stock: bool = True

class ProductCreate(ProductBase):
    id: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    stock: Optional[int] = None
    in_stock: Optional[bool] = None
    is_popular: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_deal: Optional[bool] = None

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category_name: Optional[str] = None

class ProductFilterParams(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[Decimal] = None
    in_stock: Optional[bool] = None
    sort: Optional[str] = "relevance"
    cursor: Optional[str] = None
    limit: int = Field(12, ge=1, le=100)
