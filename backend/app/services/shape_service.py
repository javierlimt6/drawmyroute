import json
import math
from pathlib import Path
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.map_matcher import snap_to_roads
from app.services.llm_service import generate_svg_from_prompt
from app.services.osrm_router import snap_to_roads_osrm
from app.config import settings

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
    W_FIDELITY = 0.60   # Shape quality is king
    W_CLOSURE = 0.20    # Loop matters for running
    W_EFFICIENCY = 0.20 # Distance is nice-to-have
    
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
    shape_id: str | None,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    prompt: str | None = None,
    aspect_ratio: float = 1.0
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
    
    # Calculate distance-proportional radius
    # Higher multiplier = more flexibility, less overlap
    # For 5km: base=150m, for 20km: base=600m
    base_radius = max(100, int(distance_km * 30))  # 30m per km, min 100m
    
    print(f"   📏 Distance: {distance_km}km -> Base radius: {base_radius}m")
    
    # Strategies: High point count for shape detail
    # Larger base shape (divisor 4.0) prevents zig-zags
    strategies = [
        # Maximum Fidelity - 50 points (chunked routing)
        {"points": 50, "radius": base_radius,       "profile": "walking", "fidelity": 1.0},
        {"points": 50, "radius": base_radius * 2,   "profile": "walking", "fidelity": 0.95},
        
        # High Fidelity - 40 points
        {"points": 40, "radius": base_radius * 2,   "profile": "walking", "fidelity": 0.85},
        {"points": 40, "radius": base_radius * 3,   "profile": "walking", "fidelity": 0.80},
        
        # Fallback - 30 points
        {"points": 30, "radius": base_radius * 3,   "profile": "walking", "fidelity": 0.65},
        
        # Cycling fallback
        {"points": 40, "radius": base_radius * 3,   "profile": "cycling", "fidelity": 0.50},
        
        # Last Resort
        {"points": 20, "radius": base_radius * 5,   "profile": "walking", "fidelity": 0.30},
    ]
    
    # === ITERATIVE SCALING ===
    # Try to match target distance by adjusting scale factor
    MAX_ITERATIONS = 3
    TOLERANCE = 0.25  # Accept if within 25% of target
    
    scale_factor = 1.0
    best_overall = None
    
    print(f"🔄 Generating '{current_shape_id}' ({distance_km}km) at {start_lat}, {start_lng}")
    
    for iteration in range(MAX_ITERATIONS):
        successful_results = []
        last_error = None
        
        print(f"   🔁 Iteration {iteration + 1}/{MAX_ITERATIONS} (scale: {scale_factor:.2f})")
        
        for strategy in strategies:
            try:
                # 1. Parse & Scale with current scale_factor
                abstract_points = sample_svg_path(svg_path, num_points=strategy["points"])
                gps_points = scale_to_gps(abstract_points, start_lat, start_lng, distance_km, scale_factor, aspect_ratio=aspect_ratio)
                
                # 2. Try to map match
                result = await snap_to_roads(
                    gps_points, 
                    profile=strategy["profile"], 
                    radius=strategy["radius"]
                )
                
                # 3. Calculate Score
                score = calculate_score(result, distance_km, strategy)
                
                result_data = {
                    "shape_id": shape_id,
                    "shape_name": shapes[shape_id]["name"],
                    "input_prompt": prompt,
                    "original_points": abstract_points,
                    "gps_points": gps_points,
                    "score": score,
                    "strategy": strategy,
                    "scale_factor": scale_factor,
                    **result
                }
                
                successful_results.append(result_data)
                print(f"      ✅ {strategy['points']}pts -> Score: {score:.1f}, Dist: {result['distance_m']:.0f}m")
                
                # Early exit if score is great
                if strategy["fidelity"] >= 0.9 and score > 80.0:
                    break
                
            except Exception as e:
                last_error = e
                continue
        
        if not successful_results:
            if iteration == MAX_ITERATIONS - 1:
                raise ValueError(f"Could not generate route. Last error: {last_error}")
            continue
        
        # Pick the best result from this iteration
        best_result = max(successful_results, key=lambda x: x["score"])
        actual_dist_km = best_result["distance_m"] / 1000.0
        distance_ratio = actual_dist_km / distance_km
        
        print(f"      📊 Target: {distance_km}km, Actual: {actual_dist_km:.1f}km, Ratio: {distance_ratio:.2f}")
        
        # Check if within tolerance
        if abs(distance_ratio - 1.0) <= TOLERANCE:
            print(f"   ✅ Within tolerance ({TOLERANCE*100:.0f}%), accepting result")
            best_overall = best_result
            break
        
        # Update best overall if this is better
        if best_overall is None or best_result["score"] > best_overall["score"]:
            best_overall = best_result
        
        # Adjust scale factor for next iteration
        # If route is too long, make shape smaller; if too short, make shape bigger
        adjustment = distance_km / actual_dist_km
        # Dampen the adjustment to avoid overshooting
        scale_factor *= (1.0 + (adjustment - 1.0) * 0.7)
        scale_factor = max(0.2, min(3.0, scale_factor))  # Clamp to reasonable range
        
        print(f"   🔧 Adjusting scale to {scale_factor:.2f} for next iteration")
    
    if best_overall is None:
        raise ValueError("Could not generate route after all iterations")
    
    best_result = best_overall
    print(f"🏆 Best result: Score {best_result['score']:.2f}, Dist: {best_result['distance_m']:.0f}m")
    
    # Calculate distance from user's position to route start and back
    route_coords = best_result["route"]["coordinates"]
    if route_coords:
        route_start = route_coords[0]   # [lng, lat]
        route_end = route_coords[-1]    # [lng, lat]
        
        # Haversine-like approximation for short distances
        def calc_distance_m(lat1, lng1, lat2, lng2):
            dlat = (lat2 - lat1) * 111320  # meters per degree lat
            dlng = (lng2 - lng1) * 111320 * math.cos(math.radians(lat1))
            return math.sqrt(dlat**2 + dlng**2)
        
        # Distance from user to route start
        approach_m = calc_distance_m(start_lat, start_lng, route_start[1], route_start[0])
        # Distance from route end back to user
        return_m = calc_distance_m(route_end[1], route_end[0], start_lat, start_lng)
        
        best_result["approach_distance_m"] = round(approach_m, 1)
        best_result["return_distance_m"] = round(return_m, 1)
        best_result["total_with_travel_m"] = round(best_result["distance_m"] + approach_m + return_m, 1)
        
        print(f"   📍 Approach: {approach_m:.0f}m, Return: {return_m:.0f}m")
        print(f"🏁 Shape: {best_result['distance_m']:.0f}m, Total w/ travel: {best_result['total_with_travel_m']:.0f}m")
    else:
        best_result["approach_distance_m"] = 0
        best_result["return_distance_m"] = 0
        best_result["total_with_travel_m"] = best_result["distance_m"]
        print(f"🏁 Final: {best_result['strategy']['points']}pts, Dist: {best_result['distance_m']:.0f}m")
    
    # Add debug info to response
    best_result["debug_log"] = [
        f"Strategy {r['strategy']['points']}pts/{r['strategy']['radius']}m -> Score: {r['score']:.1f}"
        for r in successful_results
    ]
    best_result["algorithm"] = "mapbox"
    
    return best_result


async def generate_route_osrm(
    shape_id: str | None,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    prompt: str | None = None,
    aspect_ratio: float = 1.0,
    fast_mode: bool = False
) -> dict:
    """
    Generate route using OSRM with multi-variant optimization.
    Tests multiple rotations and sizes in parallel to find the best fit.
    fast_mode: Skip optimization for faster resize response.
    """
    import asyncio
    
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
    
    # Fast mode: Single variant with fewer points for resize
    if fast_mode:
        NUM_POINTS = 40  # Fewer points for speed
        ROTATIONS = [0]
        SCALE_FACTORS = [1.0]
        print(f"⚡ [OSRM Fast] Generating '{current_shape_id}' ({distance_km}km)")
    else:
        NUM_POINTS = 80  # Higher point count for smoother curves
        ROTATIONS = [0, 90]  # Reduced from 4 to 2 for speed
        # Wider scale range: smaller values help when roads add more distance
        SCALE_FACTORS = [0.5, 0.7, 0.9, 1.0, 1.1]  # 5 values for 10 total variants
        print(f"🔄 [OSRM Multi-Variant] Generating '{current_shape_id}' ({distance_km}km)")
    
    # Parse SVG once
    abstract_points = sample_svg_path(svg_path, num_points=NUM_POINTS)
    
    # Generate all variant combinations
    variants = []
    for rotation in ROTATIONS:
        for scale in SCALE_FACTORS:
            variants.append({
                "rotation": rotation,
                "scale": scale,
                "label": f"R{rotation}°/S{scale}"
            })
    
    print(f"   🔀 Testing {len(variants)} variants ({len(ROTATIONS)} rotations × {len(SCALE_FACTORS)} sizes)")
    
    # Quality thresholds (relaxed since perimeter-based is more accurate)
    MAX_FAILED_SEGMENT_RATIO = 0.20  # Max 20% failed segments (roads may not exist)
    MAX_DISTANCE_RATIO = 1.8         # Route can't be >1.8x target
    MIN_DISTANCE_RATIO = 0.5         # Route can't be <50% of target
    MIN_ACCEPTABLE_SCORE = 40.0      # Minimum score to accept
    
    async def evaluate_variant(variant: dict) -> dict:
        """Evaluate a single variant and return result with score."""
        try:
            # Scale with rotation and size
            gps_points = scale_to_gps(
                abstract_points,
                start_lat, start_lng,
                distance_km,
                scale_factor=variant["scale"],
                rotation_deg=variant["rotation"],
                aspect_ratio=aspect_ratio
            )
            
            # Route using OSRM
            result = await snap_to_roads_osrm(gps_points, profile="foot")
            
            # --- QUALITY CHECKS ---
            failed_ratio = result.get("failed_segments", 0) / result.get("total_segments", 1)
            actual_km = result["distance_m"] / 1000.0
            distance_ratio = actual_km / distance_km
            
            # Check if this variant is acceptable
            rejection_reasons = []
            if failed_ratio > MAX_FAILED_SEGMENT_RATIO:
                rejection_reasons.append(f"too many failed segments ({failed_ratio*100:.0f}%)")
            if distance_ratio > MAX_DISTANCE_RATIO:
                rejection_reasons.append(f"route too long ({distance_ratio:.1f}x target)")
            if distance_ratio < MIN_DISTANCE_RATIO:
                rejection_reasons.append(f"route too short ({distance_ratio:.1f}x target)")
            
            if rejection_reasons:
                return {
                    "success": False, 
                    "variant": variant, 
                    "error": "; ".join(rejection_reasons),
                    "distance_m": result["distance_m"],
                    "failed_ratio": failed_ratio
                }
            
            # Calculate score
            strategy = {"points": NUM_POINTS, "fidelity": 1.0, "profile": "foot"}
            score = calculate_score(result, distance_km, strategy)
            
            # Penalize based on failed segments and distance accuracy
            distance_accuracy = 1.0 - abs(distance_ratio - 1.0)
            segment_quality = 1.0 - failed_ratio
            adjusted_score = score * (0.5 + 0.25 * max(0, distance_accuracy) + 0.25 * segment_quality)
            
            return {
                "success": True,
                "variant": variant,
                "gps_points": gps_points,
                "result": result,
                "score": adjusted_score,
                "distance_m": result["distance_m"],
                "failed_ratio": failed_ratio
            }
        except Exception as e:
            return {"success": False, "variant": variant, "error": str(e)}
    
    # Run all variants in parallel
    results = await asyncio.gather(*[evaluate_variant(v) for v in variants])
    
    # Filter successful results that meet minimum score
    successful = [r for r in results if r.get("success") and r.get("score", 0) >= MIN_ACCEPTABLE_SCORE]
    rejected = [r for r in results if not r.get("success")]
    
    # Log rejection reasons
    if rejected:
        print(f"   ⚠️ {len(rejected)} variants rejected:")
        for r in rejected[:3]:
            print(f"      {r['variant']['label']}: {r.get('error', 'unknown')}")
    
    if not successful:
        # No good routes found
        raise ValueError(
            f"Could not find a good route for this location. "
            f"Tried {len(variants)} variants, all failed quality checks. "
            f"Try a different starting location with more walkable roads."
        )
    
    # Pick the best
    best = max(successful, key=lambda x: x["score"])
    
    # Log results
    print(f"   📊 Results: {len(successful)}/{len(variants)} passed quality checks")
    for r in sorted(successful, key=lambda x: -x["score"])[:5]:
        print(f"      {r['variant']['label']}: Score {r['score']:.1f}, Dist: {r['distance_m']:.0f}m")
    
    print(f"🏆 Best: {best['variant']['label']} (Score: {best['score']:.1f})")
    
    # Build final result
    result_data = {
        "shape_id": current_shape_id,
        "shape_name": shape_name,
        "input_prompt": prompt,
        "svg_path": svg_path,
        "original_points": abstract_points,
        "gps_points": best["gps_points"],
        "score": best["score"],
        "strategy": {
            "points": NUM_POINTS,
            "fidelity": 1.0,
            "rotation": best["variant"]["rotation"],
            "scale": best["variant"]["scale"]
        },
        "algorithm": "osrm-multivariant",
        **best["result"]
    }
    
    # Calculate approach/return distances
    route_coords = best["result"]["route"]["coordinates"]
    if route_coords:
        route_start = route_coords[0]
        route_end = route_coords[-1]
        
        def calc_distance_m(lat1, lng1, lat2, lng2):
            dlat = (lat2 - lat1) * 111320
            dlng = (lng2 - lng1) * 111320 * math.cos(math.radians(lat1))
            return math.sqrt(dlat**2 + dlng**2)
        
        approach_m = calc_distance_m(start_lat, start_lng, route_start[1], route_start[0])
        return_m = calc_distance_m(route_end[1], route_end[0], start_lat, start_lng)
        
        result_data["approach_distance_m"] = round(approach_m, 1)
        result_data["return_distance_m"] = round(return_m, 1)
        result_data["total_with_travel_m"] = round(best["result"]["distance_m"] + approach_m + return_m, 1)
    else:
        result_data["approach_distance_m"] = 0
        result_data["return_distance_m"] = 0
        result_data["total_with_travel_m"] = best["result"]["distance_m"]
    
    # Debug log
    result_data["debug_log"] = [
        f"Multi-variant: {len(variants)} candidates",
        f"Best: {best['variant']['label']}",
        f"Top 3: {', '.join(r['variant']['label'] for r in sorted(successful, key=lambda x: -x['score'])[:3])}"
    ]
    
    return result_data


async def generate_route(
    shape_id: str | None,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    prompt: str | None = None,
    aspect_ratio: float = 1.0,
    fast_mode: bool = False
) -> dict:
    """
    Main entry point for route generation.
    Selects algorithm based on ROUTING_ALGORITHM config setting.
    fast_mode: Skip multi-variant optimization for faster resize response.
    """
    algorithm = settings.ROUTING_ALGORITHM
    mode_str = "[FAST]" if fast_mode else ""
    print(f"📐 {mode_str} Using algorithm: {algorithm}, aspect_ratio: {aspect_ratio:.2f}")
    
    if algorithm == "osrm":
        return await generate_route_osrm(shape_id, start_lat, start_lng, distance_km, prompt, aspect_ratio, fast_mode)
    else:
        return await generate_route_from_shape(shape_id, start_lat, start_lng, distance_km, prompt, aspect_ratio)
