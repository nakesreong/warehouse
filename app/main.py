from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os
from . import models, database, crud, deps, mappings, schemas
from .database import engine
from .routers import auth, items, ai

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warehouse 21")

# Add Session Middleware (Secret key should be in .env in prod)
# Add Session Middleware (Secret key should be in .env in prod)
# https_only=False allows usage on localhost and HTTP over LAN
app.add_middleware(SessionMiddleware, secret_key="secret-key-warehouse-21", https_only=False, same_site="lax")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(ai.router)

# Initialize Categories
@app.on_event("startup")
def on_startup():
    db = database.SessionLocal()
    crud.init_categories(db)
    db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(deps.get_db)):
    # Check if setup needed
    if not db.query(models.User).filter(models.User.is_admin == True).first():
        return RedirectResponse(url="/setup")
    
    current_user = await deps.get_current_user(request, db)
    items_orm = crud.get_items(db)
    categories = db.query(models.Category).all()

    # Serialize items for Jinja/JSON usage
    # We use the Pydantic schema to convert specific fields and handle date serialization
    from fastapi.encoders import jsonable_encoder
    items_data = [jsonable_encoder(schemas.Item.from_orm(i)) for i in items_orm]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "items": items_data, 
        "categories": categories,
        "user": current_user,
        "cat_structure": mappings.CATEGORY_STRUCTURE
    })

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
