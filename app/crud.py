from sqlalchemy.orm import Session
from . import models, schemas
import hashlib

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False):
    fake_hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    db_user = models.User(username=user.username, hashed_password=fake_hashed_password, is_admin=is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

from . import mappings


def create_item(db: Session, item: schemas.ItemCreate):
    # Auto-assign icon based on subcategory from database
    icon_type = "pack_generic.png"  # Default
    
    if item.subcategory:
        # Try to get icon from database subcategory
        subcategory_obj = db.query(models.SubCategory).filter(
            models.SubCategory.slug == item.subcategory
        ).first()
        
        if subcategory_obj and subcategory_obj.icon_path:
            icon_type = subcategory_obj.icon_path
        elif item.subcategory in mappings.ICON_MAPPING:
            # Fallback to static mapping
            icon_type = mappings.ICON_MAPPING[item.subcategory]
    
    item.icon_type = icon_type
    
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def init_categories(db: Session):
    # Check if categories exist
    if not db.query(models.Category).first():
        cats = [
            {"name": "Еда", "slug": "food"},
            {"name": "Напитки", "slug": "drinks"},
            {"name": "Разное", "slug": "misc"},
        ]
        for c in cats:
            db_cat = models.Category(name=c["name"], slug=c["slug"])
            db.add(db_cat)
        db.commit()
    
    # Init Subcategories from mappings
    if not db.query(models.SubCategory).first():
        # Re-fetch categories to get IDs
        cat_map = {c.slug: c.id for c in db.query(models.Category).all()}
        
        for cat_slug, data in mappings.CATEGORY_STRUCTURE.items():
            cat_id = cat_map.get(cat_slug)
            if not cat_id: continue
            
            for sub_slug, sub_name in data["subs"].items():
                icon = mappings.ICON_MAPPING.get(sub_slug, "pack_generic.png")
                db_sub = models.SubCategory(
                    name=sub_name, 
                    slug=sub_slug, 
                    icon_path=icon, 
                    category_id=cat_id
                )
                db.add(db_sub)
        db.commit()

def create_subcategory(db: Session, sub: schemas.SubCategoryCreate):
    db_sub = models.SubCategory(**sub.dict())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub
