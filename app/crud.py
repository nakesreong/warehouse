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
    # Auto-assign icon based on subcategory
    if item.subcategory in mappings.ICON_MAPPING:
        item.icon_type = mappings.ICON_MAPPING[item.subcategory]
    
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def init_categories(db: Session):
    # Check if categories exist
    if db.query(models.Category).first():
        return
    
    cats = [
        {"name": "Еда", "slug": "food"},
        {"name": "Напитки", "slug": "drinks"},
        {"name": "Разное", "slug": "misc"},
    ]
    for c in cats:
        db_cat = models.Category(name=c["name"], slug=c["slug"])
        db.add(db_cat)
    db.commit()
