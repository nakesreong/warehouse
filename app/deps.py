from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from . import crud, database, models
import hashlib

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user

def require_admin(user: models.User = Depends(get_current_user)):
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user
