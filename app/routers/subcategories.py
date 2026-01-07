from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from .. import crud, schemas, deps, models
from PIL import Image
import io
import uuid
import os
import re

router = APIRouter(prefix="/api/subcategories", tags=["subcategories"])

UPLOAD_DIR = "app/static/icons"

# Transliteration map for Russian -> Latin
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def transliterate(text: str) -> str:
    """Transliterate Russian text to Latin."""
    result = []
    for char in text.lower():
        result.append(TRANSLIT_MAP.get(char, char))
    return ''.join(result)

def make_slug(name: str) -> str:
    """Create URL-safe slug from name with transliteration."""
    # Transliterate Russian to Latin
    translit = transliterate(name)
    # Replace non-alphanumeric with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', translit.strip())
    # Remove leading/trailing underscores
    slug = slug.strip('_')
    return slug

def compress_image(image_bytes: bytes) -> str:
    """Compress and resize image, save to static/icons, return filename."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB (in case of RGBA/P)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize to max 256x256 (maintaining aspect ratio? Or square? Plan said 256x256 max)
        img.thumbnail((256, 256))
        
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        img.save(filepath, "PNG", optimize=True)
        return filename
    except Exception as e:
        print(f"Image Error: {e}")
        return "pack_generic.png" # Fallback

@router.post("/", response_model=schemas.SubCategory)
async def create_subcategory(
    name: str = Form(...),
    category_id: int = Form(...),
    file: UploadFile = File(default=None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.require_admin)
):
    # Generate slug with transliteration
    slug = make_slug(name)
    
    # Check if exists in this category
    existing = db.query(models.SubCategory).filter(
        models.SubCategory.slug == slug, 
        models.SubCategory.category_id == category_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Subcategory already exists in this category")

    icon_path = "pack_generic.png"
    if file:
        content = await file.read()
        icon_path = compress_image(content)
        
    sub_in = schemas.SubCategoryCreate(
        name=name,
        slug=slug,
        category_id=category_id,
        icon_path=icon_path
    )
    
    # Save to database
    db_sub = models.SubCategory(name=sub_in.name, slug=sub_in.slug, category_id=sub_in.category_id, icon_path=sub_in.icon_path)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

@router.put("/{subcategory_id}", response_model=schemas.SubCategory)
async def update_subcategory(
    subcategory_id: int,
    name: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.require_admin)
):
    """Update subcategory name and/or icon. Icon changes propagate to all items in this subcategory."""
    # Get existing subcategory
    subcategory = db.query(models.SubCategory).filter(
        models.SubCategory.id == subcategory_id
    ).first()
    
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    # Store old slug for item updates
    old_slug = subcategory.slug
    
    # Update name and regenerate slug with transliteration
    subcategory.name = name
    new_slug = make_slug(name)
    subcategory.slug = new_slug
    
    # Update icon if provided
    icon_updated = False
    if file and file.filename:
        # Compress and save new icon
        try:
            # Ensure UPLOAD_DIR exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            img = Image.open(file.file)
            img = img.convert("RGBA")
            img.thumbnail((128, 128), Image.Resampling.LANCZOS)
            
            icon_filename = f"sub_{new_slug}.png"
            filepath = os.path.join(UPLOAD_DIR, icon_filename)
            img.save(filepath, "PNG", optimize=True)
            
            subcategory.icon_path = icon_filename
            icon_updated = True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process icon: {str(e)}")
    
    # Update all items with this subcategory (both slug and icon if changed)
    items = db.query(models.Item).filter(
        models.Item.subcategory == old_slug
    ).all()
    
    for item in items:
        # Update subcategory reference
        item.subcategory = new_slug
        # Update icon if it was changed
        if icon_updated:
            item.icon_type = subcategory.icon_path
    
    db.commit()
    db.refresh(subcategory)
    return subcategory

@router.delete("/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(
    subcategory_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.require_admin)
):
    """Delete a subcategory. Items in this subcategory will need manual reassignment."""
    subcategory = db.query(models.SubCategory).filter(
        models.SubCategory.id == subcategory_id
    ).first()
    
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    # Delete the subcategory
    db.delete(subcategory)
    db.commit()
    return None
