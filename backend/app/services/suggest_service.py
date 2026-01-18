"""
Suggest Service - Auto-suggest best routes from the shape database

Uses the same iterative scaling algorithm as regular route generation,
but tests multiple shapes in parallel to find the best fit.
"""

import asyncio
import random
from app.services.data_store_service import get_shape_by_name
from app.services.svg_parser import sample_svg_path
from app.services.geo_scaler import scale_to_gps
from app.services.osrm_router import snap_to_roads_osrm
from app.services.shape_service import calculate_score
from .data_store_service import get_random_shapes
from .route_generator import route_with_scaling, calculate_approach_distances
from .scoring import calculate_route_quality
from . import routing_config as cfg


async def evaluate_shape(
    shape_name: str,
    svg_path: str,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    aspect_ratio: float = 1.0
) -> dict:
    """
    Evaluate a single shape using iterative scaling.
    
    Returns dict with success status, score, and route data if successful.
    """
    try:
        result = await route_with_scaling(
            svg_path=svg_path,
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=distance_km,
            aspect_ratio=aspect_ratio,
            rotation_deg=0,
            num_points=cfg.POINTS_SUGGEST
        )
        
        return {
            "success": True,
            "shape_name": shape_name,
            "svg_path": svg_path,
            "gps_points": result["gps_points"],
            "result": result["result"],
            "score": result["score"],
            "distance_m": result["result"]["distance_m"],
            "scale_factor": result["scale_factor"]
        }
    except Exception as e:
        return {
            "success": False, 
            "shape_name": shape_name, 
            "error": str(e)
        }


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
    print(f"   📊 Results: {len(successful)}/{len(results)} shapes passed")
    for r in failed[:3]:
        print(f"      ❌ {r['shape_name']}: {r.get('error', 'unknown')}")
    for r in sorted(successful, key=lambda x: -x["score"])[:5]:
        print(f"      ✅ {r['shape_name']}: Score {r['score']:.1f}")
    
    if not successful:
        raise ValueError(
            f"Could not find a suitable route. Tried {len(results)} shapes. "
            "Try a different location or distance."
        )
    
    # Pick the best
    best = max(successful, key=lambda x: x["score"])
    print(f"🏆 Best: {best['shape_name']} (Score: {best['score']:.1f})")
    
    # Calculate approach/return distances
    route_coords = best["result"]["route"]["coordinates"]
    travel_distances = calculate_approach_distances(start_lat, start_lng, route_coords)
    
    # Build response
    return {
        "shape_id": best["shape_name"],
        "shape_name": best["shape_name"].replace("-", " ").title(),
        "svg_path": best["svg_path"],
        "gps_points": best["gps_points"],
        "score": best["score"],
        "algorithm": "auto-suggest",
        "rotation_deg": 0,
        
        # Route data
        **best["result"],
        
        # Travel distances
        "approach_distance_m": travel_distances["approach_distance_m"],
        "return_distance_m": travel_distances["return_distance_m"],
        
        # Suggestion metadata
        "suggestion_metadata": {
            "candidates_tried": len(results),
            "candidates_passed": len(successful),
            "alternatives": [
                {"name": r["shape_name"], "score": round(r["score"], 1)}
                for r in sorted(successful, key=lambda x: -x["score"])[:5]
            ]
        }
    }
