from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .. import deps, crud, schemas, models
import google.generativeai as genai
import os
import json

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Configure Gemini
# NOTE: In production, ensure GEMINI_API_KEY is set in environment structure.
# For this demo, we assume the user has set it or will set it.
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# System Prompt
SYSTEM_PROMPT = """
You are "Stockman", the AI Quartermaster of Warehouse 21 (a post-apocalyptic bunker).
Your persona: Grumpy but helpful, retro-futuristic, speaks in short terminal-like sentences. 
Use slang like "Ration", "Unit", "Supply".

You have access to the inventory database.
When user asks to ADD items:
1. Identify the item name and quantity.
2. Map it to one of these categories: Food (food), Drinks (drinks), Misc (misc).
3. Map it to an icon: 
   - Food: can_meat.png, can_fish.png, jar.png, bowl.png, box.png
   - Drinks: bottle_5l.png, bottle_2l.png, can_drink.png, bottle_glass.png
   - Misc: pack_generic.png
4. Call the `add_item` function.

When user asks "What to cook?":
1. Call `get_inventory` first.
2. Suggest a "wasteland recipe" based on available items.
"""

# Tool Definitions
def add_item_tool(name: str, quantity: int, category_slug: str, icon_type: str):
    """Add an item to the inventory."""
    # This is a stub for the model to see. Logic handles actual DB write.
    return f"Added {quantity} x {name} ({category_slug}) icon: {icon_type}"

def get_inventory_tool():
    """Get current inventory list."""
    return "Inventory list"

tools = [add_item_tool, get_inventory_tool]

@router.post("/chat")
async def chat(request: Request, data: dict, db: Session = Depends(deps.get_db), user: models.User = Depends(deps.require_admin)):
    if not api_key:
        return {"response": "SYSTEM ERROR: API_KEY_MISSING. CONTACT ADMIN."}
    
    user_message = data.get("message")
    history = data.get("history", [])

    try:
        model = genai.GenerativeModel('gemini-1.5-flash', tools=tools, system_instruction=SYSTEM_PROMPT)
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # In a real app, we'd rebuild history here. For simplicity, we send neutral context + message
        # But we need to handle function calls manually if we want to write to OUR DB.
        # However, Gemini Python SDK `enable_automatic_function_calling` executes the python functions if they are passed.
        # So we need to wrap our DB calls in the tool functions and pass 'db' context which is tricky with this SDK pattern in a stateless request.
        # ALTERNATIVE: Use manual function calling.
        
        # Let's use a simpler approach for this prototype: Manual Tool handling
        model_manual = genai.GenerativeModel('gemini-1.5-flash', tools=tools, system_instruction=SYSTEM_PROMPT)
        chat_manual = model_manual.start_chat()
        
        response = chat_manual.send_message(user_message)
        
        part = response.parts[0]
        
        # Handle Function Call
        if part.function_call:
            fc = part.function_call
            fname = fc.name
            args = fc.args
            
            if fname == "add_item_tool":
                # Find category
                cat = db.query(models.Category).filter(models.Category.slug == args['category_slug']).first()
                if not cat:
                    cat = db.query(models.Category).filter(models.Category.slug == 'misc').first()
                
                # Create Item
                item_in = schemas.ItemCreate(
                    name=args['name'],
                    quantity=int(args['quantity']),
                    target_quantity=10, # Default
                    icon_type=args['icon_type'],
                    category_id=cat.id
                )
                crud.create_item(db, item_in)
                
                # Response back to model
                # We simply return a confirmation message to the user for now
                return {"response": f"ACKNOWLEDGE. ADDED {args['quantity']} {args['name']}. STOCK UPDATED."}
                
            elif fname == "get_inventory_tool":
                items = crud.get_items(db)
                inventory_str = ", ".join([f"{i.name} ({i.quantity})" for i in items])
                
                # Send result back to model to generate recipe
                # We need to send the function response back.
                # Since we are not maintaining stateful chat object across requests easily here without history reconstruction:
                # We will just do a new generation with the inventory context.
                
                final_response = model_manual.generate_content(f"User asked: {user_message}. Inventory: {inventory_str}. Suggest a recipe.")
                return {"response": final_response.text}

        return {"response": response.text}

    except Exception as e:
        print(f"AI Error: {e}")
        return {"response": "COMMUNICATION FAILURE. INTERFERENCE DETECTED."}
