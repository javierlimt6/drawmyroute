from svg.path import parse_path

def sample_svg_path(svg_d: str, num_points: int = 25) -> list[tuple[float, float]]:
    """
    Parse SVG path 'd' attribute and sample evenly-spaced points.
    Returns list of (x, y) tuples in 0-100 coordinate space.
    """
    path = parse_path(svg_d)
    total_length = path.length()
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        point = path.point(t * total_length / path.length())
        points.append((point.real, point.imag))
    
    return points
