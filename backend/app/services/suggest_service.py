"""
Suggest Service - Auto-suggest best routes from the shape database
"""
import asyncio
import random
from app.services.data_store_service import get_shape_by_name
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.osrm_router import snap_to_roads_osrm
from app.services.shape_service import calculate_score


async def evaluate_shape(
    shape_name: str,
    svg_path: str,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    aspect_ratio: float = 1.0
) -> dict:
    """
    Evaluate a single shape and return result with score.
    Uses iterative scaling to force routes within 1.3x distance ratio.
    
    Returns dict with success status, score, and route data if successful.
    """
    # Use high point count for better fidelity
    NUM_POINTS = 150
    MAX_DISTANCE_RATIO = 1.3
    MIN_DISTANCE_RATIO = 0.5
    MAX_ITERATIONS = 4  # Try up to 4 scale adjustments
    
    try:
        # Parse SVG once
        abstract_points = sample_svg_path(svg_path, num_points=NUM_POINTS)
        
        scale_factor = 1.0
        best_result = None
        best_distance_ratio = float('inf')
        
        for iteration in range(MAX_ITERATIONS):
            # Scale to GPS coordinates with current scale factor
            gps_points = scale_to_gps(
                abstract_points,
                start_lat, start_lng,
                distance_km,
                scale_factor=scale_factor,
                rotation_deg=0,
                aspect_ratio=aspect_ratio
            )
            
            # Route using OSRM
            result = await snap_to_roads_osrm(gps_points, profile="foot")
            
            # Check quality
            failed_ratio = result.get("failed_segments", 0) / max(result.get("total_segments", 1), 1)
            
            # Too many failed segments - this shape doesn't work for this location
            if failed_ratio > 0.25:
                return {"success": False, "shape_name": shape_name, "error": f"too many failed segments ({failed_ratio*100:.0f}%)"}
            
            actual_km = result["distance_m"] / 1000.0
            distance_ratio = actual_km / distance_km
            
            # Check if this is the best result so far
            if abs(distance_ratio - 1.0) < abs(best_distance_ratio - 1.0):
                best_distance_ratio = distance_ratio
                best_result = {
                    "gps_points": gps_points,
                    "result": result,
                    "scale_factor": scale_factor,
                    "failed_ratio": failed_ratio
                }
            
            # Check if within acceptable range
            if MIN_DISTANCE_RATIO <= distance_ratio <= MAX_DISTANCE_RATIO:
                # Success! Within 1.3x ratio
                break
            
            # Need to adjust scale for next iteration
            # If route is too long, make shape smaller; if too short, make shape bigger
            adjustment = distance_km / actual_km
            # Dampen the adjustment to avoid overshooting
            scale_factor *= (1.0 + (adjustment - 1.0) * 0.6)
            scale_factor = max(0.3, min(2.5, scale_factor))  # Clamp to reasonable range
        
        # Use best result we found (even if not perfect)
        if best_result is None:
            return {"success": False, "shape_name": shape_name, "error": "no valid route found"}
        
        # Final distance check - accept anything within 1.5x as "usable" but prefer 1.3x
        if best_distance_ratio > 1.5 or best_distance_ratio < 0.4:
            return {"success": False, "shape_name": shape_name, "error": f"distance mismatch ({best_distance_ratio:.1f}x target after scaling)"}
        
        # Calculate score
        strategy = {"points": NUM_POINTS, "fidelity": 1.0, "profile": "foot"}
        score = calculate_score(best_result["result"], distance_km, strategy)
        
        # Adjust score based on quality - penalize if not within 1.3x
        distance_accuracy = 1.0 - abs(best_distance_ratio - 1.0)
        segment_quality = 1.0 - best_result["failed_ratio"]
        
        # Extra penalty if outside 1.3x range
        if best_distance_ratio > MAX_DISTANCE_RATIO or best_distance_ratio < MIN_DISTANCE_RATIO:
            distance_accuracy *= 0.7  # 30% penalty
        
        adjusted_score = score * (0.5 + 0.25 * max(0, distance_accuracy) + 0.25 * segment_quality)
        
        return {
            "success": True,
            "shape_name": shape_name,
            "svg_path": svg_path,
            "gps_points": best_result["gps_points"],
            "result": best_result["result"],
            "score": adjusted_score,
            "distance_m": best_result["result"]["distance_m"],
            "failed_ratio": best_result["failed_ratio"],
            "scale_factor": best_result["scale_factor"],
            "iterations": iteration + 1
        }
    except Exception as e:
        return {"success": False, "shape_name": shape_name, "error": str(e)}


async def suggest_best_route(
    start_lat: float,
    start_lng: float,
    distance_km: float,
    num_candidates: int = 10,
    aspect_ratio: float = 1.0
) -> dict:
    """
    Try multiple shapes and return the one with the best score.
    
    Algorithm:
    1. Select random shapes from CURATED WHITELIST (toilet + presets)
    2. Generate routes for each in parallel
    3. Return the route with highest score + alternatives tried
    """
    
    # Curated Whitelist
    WHITELIST = [
        "heart", "star", "triangle", "sixty7", 
        "figure8", "lightning", "merlion", 
        "banana", "snowflake", "thumbsup", "sword", "toilet"
    ]
    
    # Get shape data for all items in whitelist
    all_candidates = []
    for name in WHITELIST:
        svg = get_shape_by_name(name)
        if svg:
            all_candidates.append((name, svg))
        else:
            print(f"   ⚠️ Shape '{name}' not found in data store")
            
    # Sample if we have more than requested, otherwise use all
    if len(all_candidates) > num_candidates:
        candidate_shapes = random.sample(all_candidates, num_candidates)
    else:
        candidate_shapes = all_candidates
        
    print(f"🎲 [Auto-Suggest] Evaluating {len(candidate_shapes)} shapes from whitelist...")
    
    # Evaluate all candidates in parallel
    tasks = [
        evaluate_shape(name, svg_path, start_lat, start_lng, distance_km, aspect_ratio)
        for name, svg_path in candidate_shapes
    ]
    results = await asyncio.gather(*tasks)
    
    # Separate successful and failed results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Log results
    print(f"   📊 Results: {len(successful)}/{len(results)} shapes passed quality checks")
    for r in failed[:3]:
        print(f"      ❌ {r['shape_name']}: {r.get('error', 'unknown')}")
    for r in sorted(successful, key=lambda x: -x["score"])[:5]:
        print(f"      ✅ {r['shape_name']}: Score {r['score']:.1f}, Dist: {r['distance_m']:.0f}m")
    
    if not successful:
        raise ValueError(
            f"Could not find a suitable route. Tried {len(results)} shapes but none produced valid routes. "
            "Try a different location or distance."
        )
    
    # Pick the best
    best = max(successful, key=lambda x: x["score"])
    print(f"🏆 Best: {best['shape_name']} (Score: {best['score']:.1f})")
    
    # Build response
    result_data = {
        "shape_id": best["shape_name"],
        "shape_name": best["shape_name"].replace("-", " ").title(),
        "svg_path": best["svg_path"],
        "original_points": [],  # Not needed for response
        "gps_points": best["gps_points"],
        "score": best["score"],
        "strategy": {"points": 40, "fidelity": 1.0},
        "algorithm": "auto-suggest",
        **best["result"],
        # Include metadata about the suggestion
        "suggestion_metadata": {
            "candidates_tried": len(results),
            "candidates_passed": len(successful),
            "alternatives": [
                {"name": r["shape_name"], "score": round(r["score"], 1)}
                for r in sorted(successful, key=lambda x: -x["score"])[:5]
            ]
        }
    }
    
    return result_data
