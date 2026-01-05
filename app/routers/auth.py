from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import crud, schemas, deps, models
import hashlib

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(deps.get_db)):
    # Check if admin exists
    if db.query(models.User).filter(models.User.is_admin == True).first():
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("setup.html", {"request": request})

@router.post("/setup")
def setup_admin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(deps.get_db)
):
    if db.query(models.User).filter(models.User.is_admin == True).first():
        return RedirectResponse(url="/", status_code=303)
    
    user_in = schemas.UserCreate(username=username, password=password)
    user = crud.create_user(db, user_in, is_admin=True)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(deps.get_db)
):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user.hashed_password != hashed_password:
         return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
