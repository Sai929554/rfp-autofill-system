import io
from PIL import Image as PILImage
import os

def get_cropped_image_data(original_path: str) -> io.BytesIO:
    """
    Crops whitespace from the image and returns a BytesIO object of the cropped image.
    """
    try:
        if not os.path.exists(original_path):
            return None
            
        with PILImage.open(original_path) as img:
            # Convert to RGBA to handle transparency if present
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Get bounding box of non-zero alpha pixels
            bbox = img.getbbox()
            
            # If bbox is None (empty image), return original or empty
            if bbox:
                cropped = img.crop(bbox)
            else:
                cropped = img
            
            img_byte_arr = io.BytesIO()
            cropped.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return img_byte_arr
    except Exception as e:
        print(f"Error cropping image: {e}")
        return None
