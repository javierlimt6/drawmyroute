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
    
    # Apply Chaikin Smoothing (1 iteration is usually enough for "organic" look)
    return _chaikin_smooth(points, iterations=1)

def _chaikin_smooth(points: list[tuple[float, float]], iterations: int = 1) -> list[tuple[float, float]]:
    """
    Apply Chaikin's corner cutting algorithm to smooth the path.
    """
    if iterations <= 0 or len(points) < 3:
        return points
        
    new_points = []
    # Keep the first point
    new_points.append(points[0])
    
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i+1]
        
        # Q = 0.75*P0 + 0.25*P1
        qx = 0.75 * p0[0] + 0.25 * p1[0]
        qy = 0.75 * p0[1] + 0.25 * p1[1]
        
        # R = 0.25*P0 + 0.75*P1
        rx = 0.25 * p0[0] + 0.75 * p1[0]
        ry = 0.25 * p0[1] + 0.75 * p1[1]
        
        new_points.append((qx, qy))
        new_points.append((rx, ry))
        
    # Keep the last point
    new_points.append(points[-1])
    
    return _chaikin_smooth(new_points, iterations - 1)
