import json
from svg.path import parse_path, Move, Line, CubicBezier, QuadraticBezier, Arc, Close

def get_points_from_path(path):
    points = []
    for segment in path:
        if isinstance(segment, (Line, Move)):
            points.append((segment.start.real, segment.start.imag))
            points.append((segment.end.real, segment.end.imag))
        elif isinstance(segment, (CubicBezier, QuadraticBezier, Arc)):
            # Sample points along the curve
            for t in [i/10 for i in range(11)]:
                pt = segment.point(t)
                points.append((pt.real, pt.imag))
    return points

def normalize_points(points):
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    max_dim = max(width, height)
    
    if max_dim == 0: return [(50.0, 50.0) for _ in points]
    
    scale = 100.0 / max_dim
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    
    # Scale and center in 100x100 box while preserving aspect ratio
    return [
        ((x - center_x) * scale + 50.0, (y - center_y) * scale + 50.0)
        for x, y in points
    ]

def normalize_svg_path(svg_d):
    path = parse_path(svg_d)
    points = get_points_from_path(path)
    norm_points = normalize_points(points)
    # Reconstruct path as a polyline (for simplicity)
    d = f"M {norm_points[0][0]:.2f} {norm_points[0][1]:.2f} " + " ".join(
        f"L {x:.2f} {y:.2f}" for x, y in norm_points[1:]
    ) + " Z"
    return d

with open("drawmyroute/backend/app/data/shapes.json") as f:
    shapes = json.load(f)

for key, shape in shapes.items():
    try:
        norm_d = normalize_svg_path(shape["svg_path"])
        shape["svg_path"] = norm_d
        print(f"Normalized {key}")
    except Exception as e:
        print(f"Failed to normalize {key}: {e}")

with open("drawmyroute/backend/app/data/shapes.json", "w") as f:
    json.dump(shapes, f, indent=2)
