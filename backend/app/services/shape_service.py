import json
import math
from pathlib import Path
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.map_matcher import snap_to_roads

SHAPES_PATH = Path(__file__).parent.parent / "data" / "shapes.json"

def load_shapes() -> dict:
    with open(SHAPES_PATH) as f:
        return json.load(f)

def calculate_score(result: dict, target_distance_km: float, strategy: dict) -> float:
    """
    Weighted scoring: Fidelity > Closure > Efficiency
    Higher score is better (0-100 scale).
    """
    # Weights (sum to 1.0)
    W_FIDELITY = 0.70   # Shape quality is king
    W_CLOSURE = 0.15    # Loop matters for running
    W_EFFICIENCY = 0.15 # Distance is nice-to-have
    
    # --- Fidelity Score (0-1) ---
    fidelity_score = strategy["fidelity"]
    
    # --- Closure Score (0-1) ---
    coords = result["route"]["coordinates"]
    if not coords:
        return 0.0
    
    start_pt = coords[0]
    end_pt = coords[-1]
    
    # Euclidean distance for closure check (in degrees)
    gap_deg = math.sqrt((start_pt[0]-end_pt[0])**2 + (start_pt[1]-end_pt[1])**2)
    gap_m = gap_deg * 111000  # Convert to meters
    
    # Closure: 1.0 if gap < 10m, drops smoothly
    closure_score = 1.0 / (gap_m / 100.0 + 1.0)
    
    # --- Efficiency Score (0-1) ---
    actual_dist_km = result["distance_m"] / 1000.0
    if target_distance_km > 0:
        distance_ratio = actual_dist_km / target_distance_km
        # Accept 0.7x to 1.5x target as "good enough"
        if 0.7 <= distance_ratio <= 1.5:
            efficiency_score = 1.0 - abs(1.0 - distance_ratio) * 0.5
        else:
            efficiency_score = 0.3  # Penalty but don't kill the score
    else:
        efficiency_score = 0.5
    
    # --- Weighted Sum ---
    final_score = (
        W_FIDELITY * fidelity_score +
        W_CLOSURE * closure_score +
        W_EFFICIENCY * efficiency_score
    ) * 100
    
    return final_score

async def generate_route_from_shape(
    shape_id: str,
    start_lat: float,
    start_lng: float,
    distance_km: float
) -> dict:
    """V1: Generate route from predefined shape with Metric-Driven Selection."""
    shapes = load_shapes()
    
    if shape_id not in shapes:
        raise ValueError(f"Unknown shape: {shape_id}")
    
    svg_path = shapes[shape_id]["svg_path"]
    
    # Calculate distance-proportional radius
    # For a 5km route, base radius ~100m. For 20km route, ~400m
    # This prevents overlapping/backtracking on longer routes
    base_radius = max(50, int(distance_km * 20))  # 20m per km, min 50m
    
    print(f"   📏 Distance: {distance_km}km -> Base radius: {base_radius}m")
    
    # Strategies: Fewer points with distance-scaled radius
    # Fewer points = more spread out = less overlap
    strategies = [
        # High Fidelity - 30 points works well for most shapes
        {"points": 30, "radius": base_radius,       "profile": "walking", "fidelity": 1.0},
        {"points": 30, "radius": base_radius * 2,   "profile": "walking", "fidelity": 0.95},
        {"points": 30, "radius": base_radius * 3,   "profile": "walking", "fidelity": 0.90},
        
        # Medium Fidelity - 20 points for sparser areas
        {"points": 20, "radius": base_radius * 2,   "profile": "walking", "fidelity": 0.80},
        {"points": 20, "radius": base_radius * 4,   "profile": "walking", "fidelity": 0.70},
        
        # Fallback
        {"points": 15, "radius": base_radius * 5,   "profile": "walking", "fidelity": 0.50},
        
        # Cycling fallback (bike paths may exist where sidewalks don't)
        {"points": 20, "radius": base_radius * 3,   "profile": "cycling", "fidelity": 0.40},
        
        # Last Resort
        {"points": 10, "radius": base_radius * 10,  "profile": "walking", "fidelity": 0.20},
    ]
    
    successful_results = []
    last_error = None
    
    print(f"🔄 Generating '{shape_id}' ({distance_km}km) at {start_lat}, {start_lng}")
    
    for strategy in strategies:
        try:
            # 1. Parse & Scale
            abstract_points = sample_svg_path(svg_path, num_points=strategy["points"])
            gps_points = scale_to_gps(abstract_points, start_lat, start_lng, distance_km)
            
            # 2. Try to map match
            result = await snap_to_roads(
                gps_points, 
                profile=strategy["profile"], 
                radius=strategy["radius"]
            )
            
            # 3. Calculate Score (pass full strategy dict now)
            score = calculate_score(result, distance_km, strategy)
            
            result_data = {
                "shape_id": shape_id,
                "shape_name": shapes[shape_id]["name"],
                "original_points": abstract_points,
                "gps_points": gps_points,
                "score": score,
                "strategy": strategy,
                **result
            }
            
            successful_results.append(result_data)
            print(f"   ✅ Strategy {strategy['points']}pts/{strategy['radius']}m -> Score: {score:.2f} (Dist: {result['distance_m']:.0f}m)")
            
            # Early exit: High fidelity (≥0.9) AND good score (>75)
            # This ensures we pick a high-quality shape if it works
            if strategy["fidelity"] >= 0.9 and score > 75.0:
                 break
            
        except Exception as e:
            # print(f"   ⚠️ Strategy {strategy} failed: {e}")
            last_error = e
            continue
            
    if not successful_results:
        raise ValueError(f"Could not generate route. Last error: {last_error}")
        
    # Pick the best result
    best_result = max(successful_results, key=lambda x: x["score"])
    print(f"🏆 Best from {len(successful_results)} candidates (Score: {best_result['score']:.2f})")
    print(f"🏁 Final: {best_result['strategy']['points']}pts, Dist: {best_result['distance_m']:.0f}m")
    
    # Add debug info to response
    best_result["debug_log"] = [
        f"Strategy {r['strategy']['points']}pts/{r['strategy']['radius']}m -> Score: {r['score']:.1f}"
        for r in successful_results
    ]
    
    return best_result
