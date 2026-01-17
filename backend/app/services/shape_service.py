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
    """V1: Generate route from predefined shape with Adaptive Retry."""
    shapes = load_shapes()
    
    if shape_id not in shapes:
        raise ValueError(f"Unknown shape: {shape_id}")
    
    svg_path = shapes[shape_id]["svg_path"]
    
    # Adaptive Strategy: Try best quality first, then relax constraints
    strategies = [
        {"points": 12, "radius": 100, "profile": "walking"},  # Ideal
        {"points": 8, "radius": 200, "profile": "walking"},   # Standard
        {"points": 6, "radius": 500, "profile": "walking"},   # Relaxed
        {"points": 5, "radius": 1000, "profile": "walking"},  # Very Relaxed
        {"points": 5, "radius": 1000, "profile": "cycling"},  # Fallback Profile
    ]
    
    last_error = None
    
    for strategy in strategies:
        try:
            # 1. Parse SVG
            abstract_points = sample_svg_path(svg_path, num_points=strategy["points"])
            
            # 2. Scale to GPS
            gps_points = scale_to_gps(abstract_points, start_lat, start_lng, distance_km)
            
            # 3. Snap to roads (with specific strategy parameters)
            result = await snap_to_roads(
                gps_points, 
                profile=strategy["profile"], 
                radius=strategy["radius"]
            )
            
            # If successful, return immediately
            print(f"✅ Success with strategy: {strategy}")
            return {
                "shape_id": shape_id,
                "shape_name": shapes[shape_id]["name"],
                "original_points": abstract_points,
                "gps_points": gps_points,
                **result
            }
            
        except ValueError as e:
            print(f"⚠️ Strategy failed: {strategy} - Error: {e}")
            last_error = e
            continue
        except Exception as e:
            print(f"❌ Unexpected error with strategy {strategy}: {e}")
            last_error = e
            continue
            
    # If all strategies fail
    raise ValueError(f"Could not generate a runnable route here. Last error: {last_error}")
