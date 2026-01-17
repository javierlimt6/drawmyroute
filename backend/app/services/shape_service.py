import json
from pathlib import Path
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.map_matcher import snap_to_roads

SHAPES_PATH = Path(__file__).parent.parent / "data" / "shapes.json"

def load_shapes() -> dict:
    with open(SHAPES_PATH) as f:
        return json.load(f)

async def generate_route_from_shape(
    shape_id: str,
    start_lat: float,
    start_lng: float,
    distance_km: float
) -> dict:
    """V1: Generate route from predefined shape."""
    shapes = load_shapes()
    
    if shape_id not in shapes:
        raise ValueError(f"Unknown shape: {shape_id}")
    
    svg_path = shapes[shape_id]["svg_path"]
    
    # 1. Parse SVG to abstract points
    # Use fewer points (8) for Directions API to avoid "jagged" routes 
    # but enough to maintain shape info. Fewer points = easier to route.
    abstract_points = sample_svg_path(svg_path, num_points=8)
    
    # 2. Scale abstract points to real-world GPS
    gps_points = scale_to_gps(abstract_points, start_lat, start_lng, distance_km)
    
    # 3. Snap to roads
    result = await snap_to_roads(gps_points)
    
    return {
        "shape_id": shape_id,
        "shape_name": shapes[shape_id]["name"],
        "original_points": abstract_points,
        "gps_points": gps_points,
        **result
    }
