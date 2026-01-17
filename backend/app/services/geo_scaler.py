import math


def calculate_perimeter(points: list[tuple[float, float]]) -> float:
    """
    Calculate the perimeter of a closed shape from its points.
    Returns perimeter in the same units as the input points.
    """
    if len(points) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]  # Wrap to first point
        total += math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    return total


def scale_to_gps(
    points: list[tuple[float, float]],
    start_lat: float,
    start_lng: float,
    distance_km: float,
    scale_factor: float = 1.0,  # Multiplier to adjust size
    rotation_deg: float = 0.0,  # Rotation in degrees
    aspect_ratio: float = 1.0   # >1 = taller, <1 = wider
) -> list[tuple[float, float]]:
    """
    Convert abstract shape coordinates to GPS coordinates using perimeter-based scaling.
    
    The key insight: we calculate the abstract perimeter of the shape, then scale
    such that the resulting GPS perimeter matches the target distance (with a
    detour factor to account for road routing).
    
    Args:
        points: Abstract shape points (any coordinate system)
        start_lat: Starting latitude
        start_lng: Starting longitude
        distance_km: Target route distance in km
        scale_factor: Additional multiplier (used for variant testing)
        rotation_deg: Rotation angle in degrees
        aspect_ratio: Stretch factor (>1 = taller/narrower, <1 = shorter/wider)
    """
    # --- STEP 1: Normalize points to -0.5 to 0.5 range ---
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    # Avoid division by zero
    if width == 0: width = 1
    if height == 0: height = 1
    
    # Normalize to -0.5 to 0.5 range (centered on origin)
    normalized = [
        ((p[0] - min_x) / width - 0.5, (p[1] - min_y) / height - 0.5)
        for p in points
    ]
    
    # --- STEP 2: Apply rotation if specified ---
    if rotation_deg != 0:
        rad = math.radians(rotation_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        normalized = [
            (nx * cos_r - ny * sin_r, nx * sin_r + ny * cos_r)
            for nx, ny in normalized
        ]
    
    # --- STEP 3: Calculate abstract perimeter (in normalized units) ---
    abstract_perimeter = calculate_perimeter(normalized)
    
    # Handle edge case: if perimeter is 0, use fallback
    if abstract_perimeter < 0.01:
        abstract_perimeter = 4.0  # Assume square-like
    
    # --- STEP 4: Calculate scale to match target distance ---
    # Road detour factor: roads add ~30% to straight-line distance on average
    # This is empirical and can be tuned based on testing
    ROAD_DETOUR_FACTOR = 1.3
    
    # We want: scaled_perimeter_km * ROAD_DETOUR_FACTOR ≈ distance_km
    target_perimeter_km = distance_km / ROAD_DETOUR_FACTOR
    
    # Scale factor: how many km per unit of normalized perimeter
    km_per_unit = target_perimeter_km / abstract_perimeter
    
    # Apply user's scale_factor multiplier
    km_per_unit *= scale_factor
    
    # --- STEP 5: Apply aspect ratio adjustment ---
    # To maintain perimeter when stretching: 
    # Y grows by sqrt(aspect_ratio), X shrinks by sqrt(aspect_ratio)
    ar_factor = math.sqrt(aspect_ratio)
    scale_x_km = km_per_unit / ar_factor
    scale_y_km = km_per_unit * ar_factor
    
    # --- STEP 6: Convert to GPS coordinates ---
    deg_per_km_lat = 1 / 111.32
    lat_rad = math.radians(start_lat)
    deg_per_km_lng = 1 / (111.32 * math.cos(lat_rad))
    
    gps_points = []
    for nx, ny in normalized:
        # Invert Y: SVG Y increases downward, latitude increases upward
        lat_offset = -ny * scale_y_km * deg_per_km_lat
        lng_offset = nx * scale_x_km * deg_per_km_lng
        gps_points.append((start_lat + lat_offset, start_lng + lng_offset))
    
    return gps_points
