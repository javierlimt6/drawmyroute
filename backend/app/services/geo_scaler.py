import math

def scale_to_gps(
    points: list[tuple[float, float]],
    start_lat: float,
    start_lng: float,
    distance_km: float
) -> list[tuple[float, float]]:
    """
    Convert 0-100 abstract coordinates to GPS coordinates.
    Uses dynamic longitude scaling to prevent distortion.
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
    # Earth radius approximation (km)
    R = 6378.137
    
    # Degrees per km (latitude is constant-ish)
    deg_per_km_lat = 1 / 111.32
    
    # Degrees per km (longitude depends on latitude)
    # Use start_lat for the conversion
    lat_rad = math.radians(start_lat)
    deg_per_km_lng = 1 / (111.32 * math.cos(lat_rad))
    
    # Calculate bounding box diagonal in abstract space (hypotenuse)
    # We want this diagonal to roughly match the requested distance
    # Factor 4.0 is a heuristic: perimeter is approx 3-4x the diagonal/diameter
    target_diagonal_km = distance_km / 3.5
    
    # Apply scaling
    gps_points = []
    for nx, ny in normalized:
        # Scale x (width) and y (height) relative to target size
        # Since we normalized to 0-1, we simply multiply by target size in degrees
        
        # We assume the abstract shape is "square" in aspect ratio for simplicity of scaling,
        # preserving the original aspect ratio of the SVG.
        
        # Calculate offsets in km
        # Maintain aspect ratio: width/height ratio from SVG
        aspect_ratio = width / height
        
        if aspect_ratio > 1:
            # Wider than tall
            scale_x_km = target_diagonal_km
            scale_y_km = target_diagonal_km / aspect_ratio
        else:
            # Taller than wide
            scale_y_km = target_diagonal_km
            scale_x_km = target_diagonal_km * aspect_ratio

        lat_offset = ny * scale_y_km * deg_per_km_lat
        lng_offset = nx * scale_x_km * deg_per_km_lng
        
        gps_points.append((start_lat + lat_offset, start_lng + lng_offset))
    
    return gps_points
