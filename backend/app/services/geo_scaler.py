import math
from . import routing_config as cfg


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
    
    # Determine max dimension to preserve aspect ratio
    max_dim = max(width, height)
    if max_dim == 0: max_dim = 1
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # Normalize centered on origin, scaling by the largest dimension
    # This ensures a shape fits within a 1x1 box but keeps its proportions
    normalized = [
        ((p[0] - center_x) / max_dim, (p[1] - center_y) / max_dim)
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
    # Use centralized road detour factor from config
    # We want: scaled_perimeter_km * ROAD_DETOUR_FACTOR ≈ distance_km
    target_perimeter_km = distance_km / cfg.ROAD_DETOUR_FACTOR
    
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


def scale_to_bounds(
    points: list[tuple[float, float]],
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    rotation_deg: float = 0.0,
) -> list[tuple[float, float]]:
    """
    Scale abstract shape points to fit EXACTLY within the specified GPS bounds.
    
    This is the authoritative scaling function - the resulting points will fill
    the bounding box exactly. The user's box dimensions are respected without
    any recalculation or "optimization".
    
    Args:
        points: Abstract shape points (any coordinate system)
        min_lat, max_lat, min_lng, max_lng: Target GPS bounding box
        rotation_deg: Rotation angle in degrees
    
    Returns:
        List of (lat, lng) GPS coordinates that fit exactly in the bounds
    """
    # --- STEP 1: Normalize points to 0-1 range ---
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    src_min_x, src_max_x = min(xs), max(xs)
    src_min_y, src_max_y = min(ys), max(ys)
    
    src_width = src_max_x - src_min_x
    src_height = src_max_y - src_min_y
    
    # Avoid division by zero
    if src_width == 0: src_width = 1
    if src_height == 0: src_height = 1
    
    # Normalize to 0-1 range
    normalized = [
        ((p[0] - src_min_x) / src_width, (p[1] - src_min_y) / src_height)
        for p in points
    ]
    
    # --- STEP 2: Apply rotation if specified (around center) ---
    if rotation_deg != 0:
        rad = math.radians(rotation_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        # Center at 0.5, 0.5
        normalized = [
            (
                0.5 + (nx - 0.5) * cos_r - (ny - 0.5) * sin_r,
                0.5 + (nx - 0.5) * sin_r + (ny - 0.5) * cos_r
            )
            for nx, ny in normalized
        ]
    
    # --- STEP 3: Map directly to target GPS bounds ---
    # Note: SVG Y increases downward, latitude increases upward, so we invert Y
    lat_range = max_lat - min_lat
    lng_range = max_lng - min_lng
    
    gps_points = []
    for nx, ny in normalized:
        # Invert Y: ny=0 -> max_lat, ny=1 -> min_lat
        lat = max_lat - ny * lat_range
        lng = min_lng + nx * lng_range
        gps_points.append((lat, lng))
    
    return gps_points
