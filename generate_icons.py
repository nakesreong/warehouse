from PIL import Image, ImageDraw, ImageFont
import os

ICON_DIR = "app/static/icons"
os.makedirs(ICON_DIR, exist_ok=True)

icons = {
    "can_meat.png": ("MEAT", "#8B4513"),
    "can_fish.png": ("FISH", "#4682B4"),
    "jar.png": ("JAR", "#FFFacd"),
    "bowl.png": ("BOWL", "#DEB887"),
    "box.png": ("BOX", "#D2691E"),
    "bottle_5l.png": ("H2O", "#00FFFF"),
    "bottle_2l.png": ("SODA", "#FF69B4"),
    "can_drink.png": ("CAN", "#32CD32"),
    "bottle_glass.png": ("ALCO", "#800080"),
    "pack_generic.png": ("ITEM", "#808080")
}

def generate_icon(filename, text, color):
    # Create a 64x64 transparent image
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw background circle/box
    draw.rectangle([4, 4, 60, 60], fill=color, outline="white", width=2)
    
    # Draw Text (Simple fallback if no font)
    # Since we might not have fonts, we'll just draw a cross or simple shape for now
    # to avoid "OSError: cannot open resource"
    
    # We will just save colored squares for simplicity
    img.save(os.path.join(ICON_DIR, filename))

if __name__ == "__main__":
    for name, (txt, col) in icons.items():
        generate_icon(name, txt, col)
    print("Icons generated.")
