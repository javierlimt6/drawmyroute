import json
from svg.path import parse_path, Move, Line, CubicBezier, QuadraticBezier, Arc, Close

def get_points_from_path(path):
    points = []
    for segment in path:
        if isinstance(segment, (Line, Move)):
            points.append((segment.start.real, segment.start.imag))
            points.append((segment.end.real, segment.end.imag))
        elif isinstance(segment, (CubicBezier, QuadraticBezier, Arc)):
            for t in [i/10 for i in range(11)]:
                pt = segment.point(t)
                points.append((pt.real, pt.imag))
    return points

def normalize_points(points):
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    def norm(x, min_, max_): return ((x - min_) / (max_ - min_)) * 100 if max_ > min_ else 50
    return [(norm(x, min_x, max_x), norm(y, min_y, max_y)) for x, y in points]

def normalize_svg_path(svg_d):
    path = parse_path(svg_d)
    points = get_points_from_path(path)
    norm_points = normalize_points(points)
    d = f"M {norm_points[0][0]:.2f} {norm_points[0][1]:.2f} " + " ".join(
        f"L {x:.2f} {y:.2f}" for x, y in norm_points[1:]
    ) + " Z"
    return d

with open("drawmyroute/backend/app/data/data_store.json") as f:
    data_store = json.load(f)

for key, svg_d in data_store.items():
    try:
        norm_d = normalize_svg_path(svg_d)
        data_store[key] = norm_d
        print(f"Normalized {key}")
    except Exception as e:
        print(f"Failed to normalize {key}: {e}")

with open("drawmyroute/backend/app/data/data_store.json", "w") as f:
    json.dump(data_store, f, indent=2)
