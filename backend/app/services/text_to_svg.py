"""
Text to SVG Path Conversion Service - Skeleton/Centerline Version
Generates multi-stroke paths suitable for route drawing
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
import cv2


DEFAULT_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/System/Library/Fonts/SFNSMono.ttf",   # macOS SF Mono
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
]


def find_font() -> str:
    for font_path in DEFAULT_FONTS:
        if os.path.exists(font_path):
            return font_path
    raise FileNotFoundError("No suitable font found.")


def text_to_svg_path(text: str, font_path: str | None = None) -> str:
    """
    Convert text to skeleton SVG path with multiple strokes.
    Uses image rendering + skeletonization for centerline paths.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    text = text.strip().upper()
    
    if font_path is None:
        font_path = find_font()
    
    # Render text to image
    font_size = 200
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()
    
    # Get text bounding box
    dummy_img = Image.new('L', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0] + 40
    text_height = bbox[3] - bbox[1] + 40
    
    # Create image with white background, draw black text
    img = Image.new('L', (text_width, text_height), 255)
    draw = ImageDraw.Draw(img)
    draw.text((20 - bbox[0], 20 - bbox[1]), text, font=font, fill=0)
    
    # Convert to binary (text = True, background = False)
    img_array = np.array(img)
    binary = img_array < 128
    
    # Skeletonize to get centerline
    skeleton = skeletonize(binary)
    skeleton_uint8 = (skeleton * 255).astype(np.uint8)
    
    # Find contours in skeleton - each contour becomes a separate stroke
    contours, _ = cv2.findContours(skeleton_uint8, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        raise ValueError(f"Could not generate skeleton for '{text}'")
    
    # Build SVG path with multiple strokes (M...L... for each contour)
    all_paths = []
    for contour in contours:
        if len(contour) < 2:
            continue
        
        # Simplify contour
        epsilon = 1.5
        simplified = cv2.approxPolyDP(contour, epsilon, closed=False)
        
        if len(simplified) < 2:
            continue
        
        # Build path for this stroke
        points = [(int(p[0][0]), int(p[0][1])) for p in simplified]
        path_str = f"M {points[0][0]},{points[0][1]}"
        for p in points[1:]:
            path_str += f" L {p[0]},{p[1]}"
        all_paths.append(path_str)
    
    if not all_paths:
        raise ValueError(f"No valid paths for '{text}'")
    
    # Combine all strokes
    combined_path = " ".join(all_paths)
    
    # Normalize to 0-100 viewBox
    return normalize_path(combined_path)


def normalize_path(path_data: str) -> str:
    """Normalize path to 0-100 viewBox."""
    import re
    
    numbers = re.findall(r'-?\d+\.?\d*', path_data)
    if len(numbers) < 2:
        return path_data
    
    coords = [float(n) for n in numbers]
    x_coords = coords[::2]
    y_coords = coords[1::2]
    
    if not x_coords or not y_coords:
        return path_data
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    width = max_x - min_x or 1
    height = max_y - min_y or 1
    scale = min(90 / width, 90 / height)
    
    target_size = 100
    offset_x = (target_size - width * scale) / 2 - min_x * scale
    offset_y = (target_size - height * scale) / 2 - min_y * scale
    
    def transform(m):
        x = float(m.group(1)) * scale + offset_x
        y = float(m.group(2)) * scale + offset_y
        return f"{x:.2f},{y:.2f}"
    
    return re.sub(r'(-?\d+\.?\d*)[\s,]+(-?\d+\.?\d*)', transform, path_data)


# Cache
_text_cache: dict[str, str] = {}


def text_to_svg_path_cached(text: str) -> str:
    """Cached version of text_to_svg_path."""
    key = text.strip().upper()
    if key not in _text_cache:
        _text_cache[key] = text_to_svg_path(text)
    return _text_cache[key]


if __name__ == "__main__":
    try:
        path = text_to_svg_path("NUS")
        print(f"Generated skeleton path: {path[:300]}...")
        
        # Write test HTML
        html = f"""<!DOCTYPE html>
<html><head><title>Skeleton Text Test</title></head>
<body style="background:#333;padding:40px;">
<h1 style="color:#FC4C02;">Skeleton NUS (multi-stroke)</h1>
<svg width="400" height="200" viewBox="0 0 100 100" style="background:white;">
    <path d="{path}" fill="none" stroke="black" stroke-width="1"/>
</svg>
</body></html>"""
        with open("skeleton_test.html", "w") as f:
            f.write(html)
        print("Wrote skeleton_test.html")
    except Exception as e:
        print(f"Error: {e}")