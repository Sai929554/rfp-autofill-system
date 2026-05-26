import os
import sys

# Define the path strictly as user provided
path = r"C:\Users\saiku\.gemini\antigravity\scratch\rfp-autofill-system\backend\static\signature.png"

print(f"Checking path: {path}")
if os.path.exists(path):
    print("SUCCESS: File exists.")
else:
    print("FAILURE: File NOT found.")

# Try importing PIL
try:
    from PIL import Image
    print("SUCCESS: Pillow (PIL) is installed.")
except ImportError:
    print("FAILURE: Pillow (PIL) is NOT installed. Please install it.")
    sys.exit(1)

# Try opening and cropping
try:
    with Image.open(path) as img:
        print(f"Image opened. Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        bbox = img.getbbox()
        print(f"Bounding Box: {bbox}")
        if bbox:
            cropped = img.crop(bbox)
            print(f"Cropped Size: {cropped.size}")
        else:
            print("Image is empty (transparent)?")
except Exception as e:
    print(f"FAILURE: Error processing image: {e}")
