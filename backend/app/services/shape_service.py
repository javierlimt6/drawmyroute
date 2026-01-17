import json
import math
from pathlib import Path
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.map_matcher import snap_to_roads
from app.services.llm_service import generate_svg_from_prompt

SHAPES_PATH = Path(__file__).parent.parent / "data" / "shapes.json"

def load_shapes() -> dict:
    with open(SHAPES_PATH) as f:
        return json.load(f)

def calculate_score(result: dict, target_distance_km: float, strategy_fidelity: float) -> float:
    """
    Score a generated route based on quality metrics and strategy fidelity.
    Higher score is better.
    """
    # Metric 1: Distance match (Efficiency)
    actual_dist_km = result["distance_m"] / 1000.0
    distance_diff = abs(actual_dist_km - target_distance_km)
    
    # We want route length to be close to target. 
    # Sigmoid-like decay: 1.0 at diff=0, 0.5 at diff=1km
    efficiency_score = 1.0 / (distance_diff + 1.0)
    
    # Metric 2: Circuit Closure
    coords = result["route"]["coordinates"]
    if not coords:
        return 0.0
    
    start_pt = coords[0]
    end_pt = coords[-1]
    
    # Simple euclidean distance for closure check (approx degrees)
    gap_deg = math.sqrt((start_pt[0]-end_pt[0])**2 + (start_pt[1]-end_pt[1])**2)
    # Convert approx deg to meters (roughly)
    gap_m = gap_deg * 111000 
    
    # Closure score: 1.0 if gap < 10m, drops as gap increases
    closure_score = 1.0 / (gap_m / 100.0 + 1.0)
    
    # Combined Score = Efficiency * Closure * Fidelity
    # Fidelity penalty ensures we prefer "better shaped" routes (high points/low radius)
    # even if a "loose" route matches distance slightly better.
    final_score = efficiency_score * closure_score * strategy_fidelity * 100
    
    return final_score

async def generate_route_from_shape(
    shape_id: str | None,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    prompt: str | None = None
) -> dict:
    """V1: Generate route from predefined shape OR custom prompt."""
    
    # Logic Branch: Custom vs Predefined
    if prompt:
        print(f"✨ Custom Prompt: {prompt}")
        svg_path = generate_svg_from_prompt(prompt, distance_km)
        shape_name = f"Custom: {prompt}"
        current_shape_id = "custom"
    elif shape_id:
        shapes = load_shapes()
        if shape_id not in shapes:
            raise ValueError(f"Unknown shape: {shape_id}")
        svg_path = shapes[shape_id]["svg_path"]
        shape_name = shapes[shape_id]["name"]
        current_shape_id = shape_id
    else:
        raise ValueError("No shape specified")
    
    # Strategies: 10 variations from Perfect to Desperate
    # Fidelity: 1.0 (Best) -> 0.5 (Worst)
    strategies = [
        # High Fidelity (Sharp Shape)
        {"points": 16, "radius": 50,  "profile": "walking", "fidelity": 1.0},
        {"points": 16, "radius": 100, "profile": "walking", "fidelity": 0.95},
        
        # Standard (Balanced)
        {"points": 12, "radius": 100, "profile": "walking", "fidelity": 0.9},
        {"points": 12, "radius": 200, "profile": "walking", "fidelity": 0.85},
        
        # Simpler Shapes (Less Detailed)
        {"points": 10, "radius": 200, "profile": "walking", "fidelity": 0.8},
        {"points": 8,  "radius": 300, "profile": "walking", "fidelity": 0.75},
        
        # Loose/Fallback (Very Forgiving)
        {"points": 6,  "radius": 500, "profile": "walking", "fidelity": 0.6},
        
        # Alternative Profiles (Bike paths might exist where sidewalks don't)
        {"points": 12, "radius": 200, "profile": "cycling", "fidelity": 0.6},
        {"points": 8,  "radius": 500, "profile": "cycling", "fidelity": 0.5},
        
        # Last Resort
        {"points": 5,  "radius": 1000, "profile": "walking", "fidelity": 0.4},
    ]
    
    successful_results = []
    last_error = None
    
    print(f"🔄 Generating '{current_shape_id}' ({distance_km}km) at {start_lat}, {start_lng}")
    
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
            
            # 3. Calculate Score
            score = calculate_score(result, distance_km, strategy["fidelity"])
            
            result_data = {
                "shape_id": current_shape_id,
                "shape_name": shape_name,
                "svg_path": svg_path,
                "original_points": abstract_points,
                "gps_points": gps_points,
                "score": score,
                "strategy": strategy,
                **result
            }
            
            successful_results.append(result_data)
            print(f"   ✅ Strategy {strategy['points']}pts/{strategy['radius']}m -> Score: {score:.2f} (Dist: {result['distance_m']:.0f}m)")
            
            # Stop if we found a "Great" match (Score > 80)
            # This prevents wasting API calls if the first try was perfect.
            if score > 80.0:
                 break
            
        except Exception as e:
            # print(f"   ⚠️ Strategy {strategy} failed: {e}")
            last_error = e
            continue
            
    if not successful_results:
        raise ValueError(f"Could not generate route. Last error: {last_error}")
        
    # Pick the best result
    best_result = max(successful_results, key=lambda x: x["score"])
    print(f"🏆 Selected best route from {len(successful_results)} candidates (Score: {best_result['score']:.2f})")
    
    # Add debug info to response so frontend/client can see it
    best_result["debug_log"] = [
        f"Strategy {r['strategy']['points']}pts/{r['strategy']['radius']}m -> Score: {r['score']:.1f}"
        for r in successful_results
    ]
    
    return best_result
