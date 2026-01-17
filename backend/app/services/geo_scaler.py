import math

def scale_to_gps(
    points: list[tuple[float, float]],
    start_lat: float,
    start_lng: float,
    distance_km: float,
    scale_factor: float = 1.0,  # Multiplier to adjust size
    rotation_deg: float = 0.0   # Rotation in degrees (0, 45, 90, 135)
) -> list[tuple[float, float]]:
    """
    Convert 0-100 abstract coordinates to GPS coordinates.
    Supports rotation and scaling for multi-variant optimization.
    
    Args:
        points: Abstract shape points
        start_lat: Starting latitude
        start_lng: Starting longitude
        distance_km: Target route distance in km
        scale_factor: Multiplier to adjust shape size
        rotation_deg: Rotation angle in degrees (clockwise)
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
    
    # 2. Apply rotation if specified
    if rotation_deg != 0:
        rad = math.radians(rotation_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        normalized = [
            (nx * cos_r - ny * sin_r, nx * sin_r + ny * cos_r)
            for nx, ny in normalized
        ]
    
    # 3. Calculate scaling factors
    deg_per_km_lat = 1 / 111.32
    lat_rad = math.radians(start_lat)
    deg_per_km_lng = 1 / (111.32 * math.cos(lat_rad))
    
    # Target diagonal with scale factor
    target_diagonal_km = (distance_km / 4.0) * scale_factor
    
    # 4. Apply scaling to GPS
    gps_points = []
    aspect_ratio = width / height
    
    if aspect_ratio > 1:
        scale_x_km = target_diagonal_km
        scale_y_km = target_diagonal_km / aspect_ratio
    else:
        scale_y_km = target_diagonal_km
        scale_x_km = target_diagonal_km * aspect_ratio

    for nx, ny in normalized:
        lat_offset = ny * scale_y_km * deg_per_km_lat
        lng_offset = nx * scale_x_km * deg_per_km_lng
        gps_points.append((start_lat + lat_offset, start_lng + lng_offset))
    
    return gps_points


