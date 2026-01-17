"""
Comparison script: generates HTML to visualize current vs original text-to-svg approaches
"""

import os
from svgpathtools import wsvg, Line, QuadraticBezier, Path
from freetype import Face

# Use system font
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def tuple_to_imag(t):
    return t[0] + t[1] * 1j


def original_single_char(char: str) -> str:
    """Original code (single character only)"""
    face = Face(FONT_PATH)
    face.set_char_size(48 * 64)
    face.load_char(char)
    outline = face.glyph.outline
    y = [t[1] for t in outline.points]
    outline_points = [(p[0], max(y) - p[1]) for p in outline.points]
    start, end = 0, 0
    paths = []

    for i in range(len(outline.contours)):
        end = outline.contours[i]
        points = outline_points[start:end + 1]
        points.append(points[0])
        tags = outline.tags[start:end + 1]
        tags.append(tags[0])

        segments = [[points[0], ], ]
        for j in range(1, len(points)):
            segments[-1].append(points[j])
            if tags[j] and j < (len(points) - 1):
                segments.append([points[j], ])
        for segment in segments:
            if len(segment) == 2:
                paths.append(Line(start=tuple_to_imag(segment[0]),
                                  end=tuple_to_imag(segment[1])))
            elif len(segment) == 3:
                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                             control=tuple_to_imag(segment[1]),
                                             end=tuple_to_imag(segment[2])))
            elif len(segment) == 4:
                C = ((segment[1][0] + segment[2][0]) / 2.0,
                     (segment[1][1] + segment[2][1]) / 2.0)
                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                             control=tuple_to_imag(segment[1]),
                                             end=tuple_to_imag(C)))
                paths.append(QuadraticBezier(start=tuple_to_imag(C),
                                             control=tuple_to_imag(segment[2]),
                                             end=tuple_to_imag(segment[3])))
        start = end + 1

    path = Path(*paths)
    return path.d()


def current_multi_char(text: str) -> str:
    """Current implementation (multi-character)"""
    from app.services.text_to_svg import text_to_svg_path
    return text_to_svg_path(text)


# Generate comparison
html = """<!DOCTYPE html>
<html>
<head>
    <title>Text-to-SVG Comparison</title>
    <style>
        body { font-family: system-ui; padding: 20px; background: #1a1a1a; color: #fff; }
        .container { display: flex; gap: 40px; flex-wrap: wrap; }
        .box { background: #2a2a2a; padding: 20px; border-radius: 12px; }
        h2 { color: #FC4C02; margin-top: 0; }
        svg { background: #fff; border-radius: 8px; }
        pre { background: #333; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; max-width: 400px; }
    </style>
</head>
<body>
    <h1>Text-to-SVG Comparison</h1>
"""

# Test original (single char)
for char in ['N', 'U', 'S']:
    try:
        orig_path = original_single_char(char)
        html += f"""
    <div class="box">
        <h2>Original: '{char}'</h2>
        <svg width="200" height="200" viewBox="0 0 700 700">
            <path d="{orig_path}" fill="black"/>
        </svg>
        <pre>{orig_path[:100]}...</pre>
    </div>
"""
    except Exception as e:
        html += f'<div class="box"><h2>Original: {char}</h2><p>Error: {e}</p></div>'

# Test current (multi-char)
try:
    current_path = current_multi_char("NUS")
    html += f"""
    <div class="box">
        <h2>Current: 'NUS' (multi-char)</h2>
        <svg width="400" height="200" viewBox="0 0 100 100">
            <path d="{current_path}" fill="black"/>
        </svg>
        <pre>{current_path[:200]}...</pre>
    </div>
"""
except Exception as e:
    html += f'<div class="box"><h2>Current: NUS</h2><p>Error: {e}</p></div>'

html += """
</body>
</html>
"""

with open("text_svg_comparison.html", "w") as f:
    f.write(html)

print("Generated: text_svg_comparison.html")
