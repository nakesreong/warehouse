from pydantic import BaseModel
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True

# Category Schemas
class SubCategoryBase(BaseModel):
    name: str
    slug: str
    icon_path: str = "pack_generic.png"

class SubCategoryCreate(SubCategoryBase):
    category_id: int

class SubCategory(SubCategoryBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    slug: str

class Category(CategoryBase):
    id: int
    subcategories: List[SubCategory] = []

    class Config:
        from_attributes = True

from datetime import date

# Item Schemas
class ItemBase(BaseModel):
    name: str
    quantity: int = 0
    target_quantity: int = 0
    icon_type: str = "pack_generic.png"
    subcategory: Optional[str] = None
    expiry_date: Optional[date] = None
    category_id: int

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    category: Optional[Category] = None

    class Config:
        from_attributes = True
