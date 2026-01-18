"""
Route Generator - Unified route generation using iterative scaling

This is the core routing algorithm. It uses iterative scaling to converge
on the target distance, which is simpler and more effective than testing
multiple fixed variants.
"""

import math
from typing import Optional
from .svg_parser import sample_svg_path
from .geo_scaler import scale_to_gps
from .osrm_router import snap_to_roads_osrm
from .scoring import calculate_route_quality, is_route_acceptable
from . import routing_config as cfg


async def route_with_scaling(
    svg_path: str,
    start_lat: float,
    start_lng: float,
    distance_km: float,
    aspect_ratio: float = 1.0,
    rotation_deg: float = 0.0,
    num_points: Optional[int] = None
) -> dict:
    """
    Generate a route using iterative scaling to hit target distance.
    
    Algorithm:
    1. Sample points from SVG path
    2. Scale to GPS coordinates
    3. Route via OSRM
    4. If distance is off, adjust scale and retry (up to MAX_ITERATIONS)
    5. Return best result
    
    Args:
        svg_path: SVG path 'd' attribute string
        start_lat: Center latitude
        start_lng: Center longitude
        distance_km: Target distance in km
        aspect_ratio: Shape stretch factor (>1 = taller)
        rotation_deg: Rotation in degrees
        num_points: Override default point count
    
    Returns:
        dict with route, distance_m, score, etc.
    
    Raises:
        ValueError: If no acceptable route found
    """
    # Use default or override point count
    point_count = num_points or cfg.POINTS_DEFAULT
    
    # Sample SVG once (expensive operation)
    abstract_points = sample_svg_path(svg_path, num_points=point_count)
    
    scale_factor = 1.0
    best_result = None
    best_distance_diff = float('inf')
    
    print(f"   🔄 Route with scaling: {point_count} pts, {cfg.MAX_ITERATIONS} max iterations")
    
    for iteration in range(cfg.MAX_ITERATIONS):
        # Scale to GPS coordinates
        gps_points = scale_to_gps(
            abstract_points,
            start_lat, start_lng,
            distance_km,
            scale_factor=scale_factor,
            rotation_deg=rotation_deg,
            aspect_ratio=aspect_ratio
        )
        
        # Route via OSRM
        result = await snap_to_roads_osrm(gps_points, profile="foot")
        
        # Check basic quality
        failed_ratio = result.get("failed_segments", 0) / max(result.get("total_segments", 1), 1)
        if failed_ratio > cfg.MAX_FAILED_SEGMENT_RATIO:
            raise ValueError(f"Location has poor road coverage ({failed_ratio*100:.0f}% segments failed)")
        
        # Calculate distance ratio
        actual_km = result["distance_m"] / 1000.0
        distance_ratio = actual_km / distance_km
        distance_diff = abs(distance_ratio - 1.0)
        
        # Calculate score
        score = calculate_route_quality(result, distance_km)
        
        print(f"      Iter {iteration + 1}: scale={scale_factor:.2f}, dist={actual_km:.1f}km ({distance_ratio:.2f}x), score={score:.0f}")
        
        # Track best result
        if distance_diff < best_distance_diff:
            best_distance_diff = distance_diff
            best_result = {
                "gps_points": gps_points,
                "result": result,
                "scale_factor": scale_factor,
                "score": score,
                "distance_ratio": distance_ratio
            }
        
        # Check if good enough
        if cfg.TARGET_RATIO_MIN <= distance_ratio <= cfg.TARGET_RATIO_MAX:
            print(f"      ✅ Converged in {iteration + 1} iterations")
            break
        
        # Adaptive scaling: adjust for next iteration
        adjustment = distance_km / actual_km
        scale_factor *= (1.0 + (adjustment - 1.0) * cfg.SCALE_DAMPING)
        scale_factor = max(cfg.SCALE_MIN, min(cfg.SCALE_MAX, scale_factor))
    
    if best_result is None:
        raise ValueError("Could not generate route after all iterations")
    
    # Validate final result
    is_ok, reason = is_route_acceptable(best_result["result"], distance_km)
    if not is_ok:
        raise ValueError(f"Route failed quality check: {reason}")
    
    print(f"   🏆 Best: scale={best_result['scale_factor']:.2f}, dist={best_result['result']['distance_m']:.0f}m, score={best_result['score']:.0f}")
    
    return best_result


def calculate_approach_distances(
    start_lat: float, 
    start_lng: float, 
    route_coords: list
) -> dict:
    """
    Calculate distance from user's position to route start and back.
    
    Returns dict with approach_distance_m, return_distance_m, total_with_travel_m
    """
    if not route_coords:
        return {
            "approach_distance_m": 0,
            "return_distance_m": 0,
            "total_with_travel_m": 0
        }
    
    route_start = route_coords[0]   # [lng, lat]
    route_end = route_coords[-1]    # [lng, lat]
    
    def calc_distance_m(lat1, lng1, lat2, lng2):
        dlat = (lat2 - lat1) * 111320  # meters per degree lat
        dlng = (lng2 - lng1) * 111320 * math.cos(math.radians(lat1))
        return math.sqrt(dlat**2 + dlng**2)
    
    approach_m = calc_distance_m(start_lat, start_lng, route_start[1], route_start[0])
    return_m = calc_distance_m(route_end[1], route_end[0], start_lat, start_lng)
    
    return {
        "approach_distance_m": round(approach_m, 1),
        "return_distance_m": round(return_m, 1),
        "total_with_travel_m": 0  # Will be calculated by caller with route distance
    }


async def route_with_bounds(
    svg_path: str,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    num_points: Optional[int] = None
) -> dict:
    """
    Generate a route that fits EXACTLY within the specified GPS bounds.
    
    This is the authoritative bounds function - no iterative scaling.
    The shape is scaled to fill the bounding box, then snapped to roads.
    
    Args:
        svg_path: SVG path 'd' attribute string
        min_lat, max_lat, min_lng, max_lng: Target GPS bounding box
        num_points: Override default point count
    
    Returns:
        dict with route, distance_m, score, gps_points
    """
    from .geo_scaler import scale_to_bounds
    
    # Use default or override point count
    point_count = num_points or cfg.POINTS_DEFAULT
    
    # Sample SVG
    abstract_points = sample_svg_path(svg_path, num_points=point_count)
    
    # Scale directly to target bounds (no iterative scaling!)
    gps_points = scale_to_bounds(
        abstract_points,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        rotation_deg=0
    )
    
    print(f"   📦 Route with bounds: {point_count} pts, box=({min_lat:.4f},{min_lng:.4f})->({max_lat:.4f},{max_lng:.4f})")
    
    # Route via OSRM
    result = await snap_to_roads_osrm(gps_points, profile="foot")
    
    # Check basic quality
    failed_ratio = result.get("failed_segments", 0) / max(result.get("total_segments", 1), 1)
    if failed_ratio > cfg.MAX_FAILED_SEGMENT_RATIO:
        raise ValueError(f"Location has poor road coverage ({failed_ratio*100:.0f}% segments failed)")
    
    # Calculate score (distance ratio is N/A for bounds-based routing)
    score = calculate_route_quality(result, result["distance_m"] / 1000.0)
    
    # Calculate center for metadata
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    
    print(f"   🏆 Bounds route: dist={result['distance_m']:.0f}m, score={score:.0f}")
    
    return {
        "gps_points": gps_points,
        "result": result,
        "scale_factor": 1.0,  # N/A for bounds-based
        "score": score,
        "distance_ratio": 1.0,  # N/A for bounds-based
        "center_lat": center_lat,
        "center_lng": center_lng,
    }
