from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=128)
    slug: str = Field(..., max_length=128)
    description: Optional[str] = None
    icon: str = "Compass"
    image_url: str
    sort_order: int = 0

class CategoryCreate(CategoryBase):
    id: str

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    item_count: Optional[int] = None
