import math

def scale_to_gps(
    points: list[tuple[float, float]],
    start_lat: float,
    start_lng: float,
    distance_km: float,
    scale_factor: float = 1.0  # Multiplier to adjust size (1.0 = default, 0.5 = half size)
) -> list[tuple[float, float]]:
    """
    Convert 0-100 abstract coordinates to GPS coordinates.
    Uses dynamic longitude scaling to prevent distortion.
    
    Args:
        points: Abstract shape points
        start_lat: Starting latitude
        start_lng: Starting longitude
        distance_km: Target route distance in km
        scale_factor: Multiplier to adjust shape size (used for iterative fitting)
    """
    # 1. Normalize points to 0-1 range based on bounding box
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    # Avoid division by zero
    if width == 0: width = 1
    if height == 0: height = 1
    
    # Center points around (0,0) in 0-1 space
    normalized = [
        ((p[0] - min_x) / width - 0.5, (p[1] - min_y) / height - 0.5)
        for p in points
    ]
    
    # 2. Calculate scaling factors
    # Degrees per km (latitude is constant-ish)
    deg_per_km_lat = 1 / 111.32
    
    # Degrees per km (longitude depends on latitude)
    lat_rad = math.radians(start_lat)
    deg_per_km_lng = 1 / (111.32 * math.cos(lat_rad))
    
    # Calculate bounding box diagonal in abstract space
    # Factor 4.0: Larger shape = points further apart = less zig-zag
    # The iterative scaling will shrink if needed
    target_diagonal_km = (distance_km / 4.0) * scale_factor
    
    # Apply scaling
    gps_points = []
    for nx, ny in normalized:
        # Maintain aspect ratio
        aspect_ratio = width / height
        
        if aspect_ratio > 1:
            scale_x_km = target_diagonal_km
            scale_y_km = target_diagonal_km / aspect_ratio
        else:
            scale_y_km = target_diagonal_km
            scale_x_km = target_diagonal_km * aspect_ratio

        lat_offset = ny * scale_y_km * deg_per_km_lat
        lng_offset = nx * scale_x_km * deg_per_km_lng
        
        gps_points.append((start_lat + lat_offset, start_lng + lng_offset))
    
    return gps_points

