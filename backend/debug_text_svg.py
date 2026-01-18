"""
Debug script to understand the x_cursor issue
"""

import os
from svgpathtools import Line, QuadraticBezier, Path
from freetype import Face

FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def tuple_to_imag(t):
    return t[0] + t[1] * 1j

face = Face(FONT_PATH)
face.set_char_size(48 * 64)

text = "NUS"
x_cursor = 0

print("=== DEBUG: Character advances ===")
for char in text:
    face.load_char(char)
    advance_raw = face.glyph.advance.x
    advance_pixels = advance_raw >> 6
    
    # Get glyph metrics
    metrics = face.glyph.metrics
    width = metrics.width >> 6
    
    print(f"Char '{char}': advance.x raw = {advance_raw}, >> 6 = {advance_pixels}, width = {width}")
    print(f"  x_cursor before: {x_cursor}")
    
    outline = face.glyph.outline
    if outline.points:
        xs = [p[0] for p in outline.points]
        print(f"  outline x range: {min(xs)} to {max(xs)}")
    
    x_cursor += advance_pixels
    print(f"  x_cursor after: {x_cursor}")
    print()

print("\n=== Now generating proper multi-char path ===")

face = Face(FONT_PATH)
face.set_char_size(48 * 64)

all_paths = []
x_cursor = 0

for char in text:
    face.load_char(char)
    outline = face.glyph.outline
    
    # Copy immediately
    raw_points = [(p[0], p[1]) for p in outline.points]
    raw_tags = list(outline.tags)
    raw_contours = list(outline.contours)
    advance = face.glyph.advance.x >> 6
    
    if not raw_points:
        x_cursor += advance
        continue
    
    print(f"Processing '{char}' with x_cursor = {x_cursor}")
    
    # Flip Y and add x offset
    y_coords = [p[1] for p in raw_points]
    max_y = max(y_coords)
    outline_points = [(p[0] + x_cursor, max_y - p[1]) for p in raw_points]
    
    print(f"  After offset, x range: {min(p[0] for p in outline_points)} to {max(p[0] for p in outline_points)}")
    
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

final_path = Path(*all_paths)
path_d = final_path.d()

print(f"\nFinal path (first 300 chars):\n{path_d[:300]}")

# Write test SVG
html = f"""<!DOCTYPE html>
<html>
<head><title>Debug NUS</title></head>
<body style="background:#333;padding:40px;">
<h1 style="color:#FC4C02;">Debug: NUS multi-char</h1>
<svg width="800" height="400" viewBox="0 0 1500 700" style="background:white;">
    <path d="{path_d}" fill="black"/>
</svg>
</body>
</html>
"""

with open("debug_nus.html", "w") as f:
    f.write(html)

print("\nWrote debug_nus.html - open it to see!")
