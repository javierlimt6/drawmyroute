"""
Image to SVG Path Conversion Service
Uses Potrace for high-quality vectorization of raster images.
"""

import re
import xml.etree.ElementTree as ET
from io import BytesIO

import numpy as np
from PIL import Image
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY


def parse_svg_file(file_bytes: bytes) -> str | None:
    """
    Parse SVG file and extract path data directly.
    Returns the first valid path 'd' attribute, or None if not an SVG.
    """
    try:
        content = file_bytes.decode('utf-8', errors='ignore')
        
        if '<svg' not in content.lower():
            return None
        
        root = ET.fromstring(content)
        
        # Look for path elements (with or without namespace)
        paths = root.findall('.//{http://www.w3.org/2000/svg}path') or root.findall('.//path')
        
        if paths:
            for path in paths:
                d = path.get('d')
                if d and len(d) > 10:
                    return normalize_svg_path(d)
        
        return None
    except Exception:
        return None


def normalize_svg_path(path_d: str) -> str:
    """
    Normalize an existing SVG path to 0-100 viewBox.
    """
    numbers = re.findall(r'-?[\d.]+', path_d)
    if len(numbers) < 4:
        raise ValueError("Invalid SVG path data")
    
    coords = [float(n) for n in numbers]
    x_coords = coords[::2]
    y_coords = coords[1::2]
    
    if not x_coords or not y_coords:
        raise ValueError("Could not extract coordinates from SVG path")
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    width = max_x - min_x or 1
    height = max_y - min_y or 1
    
    scale = 90 / max(width, height)
    offset_x = (100 - width * scale) / 2
    offset_y = (100 - height * scale) / 2
    
    normalized_x = [(x - min_x) * scale + offset_x for x in x_coords]
    normalized_y = [(y - min_y) * scale + offset_y for y in y_coords]
    
    path_str = f"M {normalized_x[0]:.1f} {normalized_y[0]:.1f}"
    for i in range(1, min(len(normalized_x), len(normalized_y))):
        path_str += f" L {normalized_x[i]:.1f} {normalized_y[i]:.1f}"
    path_str += " Z"
    
    return path_str


def preprocess_image(file_bytes: bytes) -> tuple[np.ndarray, tuple[int, int]]:
    """
    Load and preprocess image for Potrace.
    Returns a binary numpy array (True = foreground, False = background)
    and the original image dimensions.
    """
    try:
        img = Image.open(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(
            "Could not open image. Supported formats: PNG, JPG, GIF, BMP. "
            "SVG files are parsed directly - make sure your SVG has a <path> element."
        ) from e
    
    # Convert to grayscale
    if img.mode != 'L':
        img = img.convert('L')
    
    # Resize if too large (Potrace handles better with reasonable sizes)
    max_dim = 1000
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to numpy array
    data = np.array(img)
    orig_shape = data.shape  # (height, width)
    
    # Add white padding around the image to prevent border detection
    # This ensures corners/edges of the image aren't traced as shapes
    padding = 20
    padded = np.full((data.shape[0] + 2*padding, data.shape[1] + 2*padding), 255, dtype=np.uint8)
    padded[padding:-padding, padding:-padding] = data
    data = padded
    
    # Auto-threshold using Otsu's method approximation
    # Use the median of non-extreme values for better threshold
    flat = data.flatten()
    threshold = np.percentile(flat, 50)  # Median
    
    # Invert if the image is mostly dark (we want dark shapes on light background)
    dark_pixels = np.sum(data < threshold)
    light_pixels = np.sum(data >= threshold)
    
    if dark_pixels > light_pixels:
        # Mostly dark image - invert so shape becomes foreground
        binary = data >= threshold
    else:
        # Mostly light image - dark areas are the shape
        binary = data < threshold
    
    # Ensure the border is always background (False) to prevent border tracing
    binary[0:padding, :] = False
    binary[-padding:, :] = False
    binary[:, 0:padding] = False
    binary[:, -padding:] = False
    
    return binary, orig_shape


def trace_with_potrace(binary: np.ndarray):
    """
    Trace binary image using Potrace.
    Returns Potrace path object.
    """
    # Create Potrace bitmap
    bitmap = Bitmap(binary)
    
    # Trace with default parameters
    path = bitmap.trace(
        turdsize=2,      # Suppress speckles of this size
        turnpolicy=POTRACE_TURNPOLICY_MINORITY,
        alphamax=1.0,    # Corner threshold
        opticurve=True,  # Optimize curves
        opttolerance=0.2
    )
    
    return path


def curves_to_svg_path(path) -> str:
    """
    Convert Potrace path curves to SVG path string.
    Uses line segments (L commands) for route compatibility.
    """
    if not path:
        raise ValueError("No paths detected in the image")
    
    # Convert path to list
    curves = list(path)
    if not curves:
        raise ValueError("No paths detected in the image")
    
    # Analyze all curves and pick the best one for a route
    # We want: high complexity (many points), not too rectangular
    best_curve = None
    best_score = 0
    
    for curve in curves:
        points = []
        start = curve.start_point
        points.append((start.x, start.y))
        
        segment_count = 0
        for segment in curve:
            segment_count += 1
            points.append((segment.end_point.x, segment.end_point.y))
            if not segment.is_corner:
                points.append((segment.c1.x, segment.c1.y))
                points.append((segment.c2.x, segment.c2.y))
        
        if len(points) < 4:
            continue
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x
        height = max_y - min_y
        
        if width < 5 or height < 5:  # Too small
            continue
        
        area = width * height
        
        # Check if it's too rectangular (likely a border)
        # Count how many points are near the corners
        corner_tolerance = max(width, height) * 0.1
        corners = [
            (min_x, min_y), (max_x, min_y),
            (max_x, max_y), (min_x, max_y)
        ]
        corner_points = 0
        for px, py in points:
            for cx, cy in corners:
                if abs(px - cx) < corner_tolerance and abs(py - cy) < corner_tolerance:
                    corner_points += 1
                    break
        
        # If more than 50% of unique points are near corners, it's likely a rectangle/border
        rectangularity = corner_points / len(points)
        if rectangularity > 0.5 and segment_count <= 6:
            continue  # Skip likely rectangular borders
        
        # Score based on complexity (segment count) and area
        # Higher segment count = more interesting shape
        score = segment_count * 10 + area * 0.01
        
        # Penalize very rectangular shapes
        aspect_ratio = max(width, height) / min(width, height)
        if segment_count <= 4 and aspect_ratio < 1.5:
            score *= 0.1  # Heavy penalty for simple rectangles/squares
        
        if score > best_score:
            best_score = score
            best_curve = curve
    
    if not best_curve:
        raise ValueError("Could not find valid curve in traced path")
    
    # Convert best curve to points
    all_points = []
    start = best_curve.start_point
    all_points.append((start.x, start.y))
    
    for segment in best_curve:
        if segment.is_corner:
            # Corner: single control point + endpoint
            all_points.append((segment.c.x, segment.c.y))
            all_points.append((segment.end_point.x, segment.end_point.y))
        else:
            # Bezier curve: sample points for better route fidelity
            all_points.append((segment.c1.x, segment.c1.y))
            all_points.append((segment.c2.x, segment.c2.y))
            all_points.append((segment.end_point.x, segment.end_point.y))
    
    if len(all_points) < 3:
        raise ValueError("Shape is too simple")
    
    # Normalize to 0-100 viewBox
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x or 1
    height = max_y - min_y or 1
    
    scale = 90 / max(width, height)
    offset_x = (100 - width * scale) / 2
    offset_y = (100 - height * scale) / 2
    
    normalized = [
        ((x - min_x) * scale + offset_x, (y - min_y) * scale + offset_y)
        for x, y in all_points
    ]
    
    # Build SVG path string
    path_d = f"M {normalized[0][0]:.1f} {normalized[0][1]:.1f}"
    for x, y in normalized[1:]:
        path_d += f" L {x:.1f} {y:.1f}"
    path_d += " Z"
    
    return path_d


def image_to_svg_path(file_bytes: bytes) -> str:
    """
    Main entry point: Convert image bytes to SVG path string.
    Handles SVG files (direct parsing) and raster images (Potrace vectorization).
    """
    # First, try to parse as SVG file
    svg_path = parse_svg_file(file_bytes)
    if svg_path:
        print("📄 Parsed SVG file directly")
        return svg_path
    
    # Otherwise, process as raster image with Potrace
    print("🖼️ Processing raster image with Potrace...")
    binary, orig_shape = preprocess_image(file_bytes)
    path = trace_with_potrace(binary)
    svg_path = curves_to_svg_path(path)
    
    return svg_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python image_to_svg.py <image_path>")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as f:
        image_bytes = f.read()
    
    try:
        svg_path = image_to_svg_path(image_bytes)
        print(f"Generated SVG path: {svg_path[:200]}...")
        print(f"Path length: {len(svg_path)} characters")
    except Exception as e:
        print(f"Error: {e}")
