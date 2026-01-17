"""
Text to SVG Path Conversion Service using FreeType
"""

import os
from svgpathtools import Line, QuadraticBezier, Path
from freetype import Face


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


def tuple_to_imag(t):
    return t[0] + t[1] * 1j


def text_to_svg_path(text: str, font_path: str | None = None) -> str:
    """Convert text to normalized SVG path using FreeType outline decomposition."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    text = text.strip().upper()
    
    if font_path is None:
        font_path = find_font()
    
    face = Face(font_path)
    face.set_char_size(48 * 64)
    
    all_paths = []
    x_cursor = 0  # In font units (NOT pixels!)
    
    for char in text:
        face.load_char(char)
        outline = face.glyph.outline
        
        # Copy points immediately (FreeType reuses the buffer)
        raw_points = [(p[0], p[1]) for p in outline.points]
        raw_tags = list(outline.tags)
        raw_contours = list(outline.contours)
        
        # Get advance in font units (NOT >> 6 which converts to pixels)
        advance = face.glyph.advance.x  # Keep in font units!
        
        if not raw_points:
            x_cursor += advance
            continue
        
        # Flip Y for this character and add x_cursor offset
        y_coords = [p[1] for p in raw_points]
        max_y = max(y_coords) if y_coords else 0
        outline_points = [(p[0] + x_cursor, max_y - p[1]) for p in raw_points]
        
        start, end = 0, 0
        
        for i in range(len(raw_contours)):
            end = raw_contours[i]
            points = outline_points[start:end + 1]
            points.append(points[0])
            tags = raw_tags[start:end + 1]
            tags.append(tags[0])
            
            segments = [[points[0]]]
            for j in range(1, len(points)):
                segments[-1].append(points[j])
                if tags[j] and j < (len(points) - 1):
                    segments.append([points[j]])
            
            for segment in segments:
                if len(segment) == 2:
                    all_paths.append(Line(
                        start=tuple_to_imag(segment[0]),
                        end=tuple_to_imag(segment[1])
                    ))
                elif len(segment) == 3:
                    all_paths.append(QuadraticBezier(
                        start=tuple_to_imag(segment[0]),
                        control=tuple_to_imag(segment[1]),
                        end=tuple_to_imag(segment[2])
                    ))
                elif len(segment) == 4:
                    C = ((segment[1][0] + segment[2][0]) / 2.0,
                         (segment[1][1] + segment[2][1]) / 2.0)
                    all_paths.append(QuadraticBezier(
                        start=tuple_to_imag(segment[0]),
                        control=tuple_to_imag(segment[1]),
                        end=tuple_to_imag(C)
                    ))
                    all_paths.append(QuadraticBezier(
                        start=tuple_to_imag(C),
                        control=tuple_to_imag(segment[2]),
                        end=tuple_to_imag(segment[3])
                    ))
            
            start = end + 1
        
        x_cursor += advance
    
    if not all_paths:
        raise ValueError(f"No paths generated for '{text}'")
    
    final_path = Path(*all_paths)
    return normalize_path(final_path.d())


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
        print(f"Generated path: {path[:200]}...")
    except Exception as e:
        print(f"Error: {e}")