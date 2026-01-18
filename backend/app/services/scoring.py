"""
Unified Route Scoring

Single function to score route quality, used by all route generation paths.
"""

import math
from . import routing_config as cfg


def haversine_distance_m(coord1: list, coord2: list) -> float:
    """
    Calculate straight-line distance between two [lng, lat] coordinates.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    lat1, lng1 = coord1[1], coord1[0]  # coords are [lng, lat]
    lat2, lng2 = coord2[1], coord2[0]
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_route_quality(result: dict, target_distance_km: float) -> float:
    """
    Score a route from 0-100. Higher is better.
    
    Components (configurable weights in routing_config.py):
    - Distance accuracy: How close to target distance (40%)
    - Road coverage: What % of segments successfully routed (40%)
    - Loop closure: How close start and end points are (20%)
    
    Args:
        result: OSRM routing result with 'route', 'distance_m', 'failed_segments', etc.
        target_distance_km: The user's requested distance
    
    Returns:
        Score from 0-100
    """
    # === DISTANCE ACCURACY ===
    actual_km = result["distance_m"] / 1000.0
    if target_distance_km > 0:
        distance_ratio = actual_km / target_distance_km
        
        # Perfect: 0.9-1.1x target
        if 0.9 <= distance_ratio <= 1.1:
            distance_score = 1.0
        # Good: 0.7-1.3x target  
        elif 0.7 <= distance_ratio <= 1.3:
            distance_score = 1.0 - abs(distance_ratio - 1.0) * 0.5
        # Acceptable: 0.5-1.5x target
        elif 0.5 <= distance_ratio <= 1.5:
            distance_score = 0.5 - abs(distance_ratio - 1.0) * 0.25
        # Poor: outside 0.5-1.5x
        else:
            distance_score = 0.2
    else:
        distance_score = 0.5
    
    # === ROAD COVERAGE ===
    total_segments = max(result.get("total_segments", 1), 1)
    failed_segments = result.get("failed_segments", 0)
    failed_ratio = failed_segments / total_segments
    coverage_score = 1.0 - failed_ratio
    
    # === LOOP CLOSURE ===
    coords = result.get("route", {}).get("coordinates", [])
    if coords and len(coords) >= 2:
        gap_m = haversine_distance_m(coords[0], coords[-1])
        # Score of 1.0 if gap < 10m, decays smoothly
        closure_score = 1.0 / (gap_m / 100.0 + 1.0)
    else:
        closure_score = 0.5
    
    # === WEIGHTED COMBINATION ===
    final_score = (
        cfg.SCORE_WEIGHT_DISTANCE * distance_score +
        cfg.SCORE_WEIGHT_COVERAGE * coverage_score +
        cfg.SCORE_WEIGHT_CLOSURE * closure_score
    ) * 100
    
    return round(final_score, 1)


def is_route_acceptable(result: dict, target_distance_km: float) -> tuple[bool, str]:
    """
    Check if a route meets minimum quality standards.
    
    Returns:
        (is_acceptable, reason_if_not)
    """
    # Check failed segment ratio
    total_segments = max(result.get("total_segments", 1), 1)
    failed_segments = result.get("failed_segments", 0)
    failed_ratio = failed_segments / total_segments
    
    if failed_ratio > cfg.MAX_FAILED_SEGMENT_RATIO:
        return False, f"too many failed segments ({failed_ratio*100:.0f}%)"
    
    # Check distance ratio
    actual_km = result["distance_m"] / 1000.0
    distance_ratio = actual_km / target_distance_km
    
    if distance_ratio > cfg.TARGET_RATIO_MAX:
        return False, f"route too long ({distance_ratio:.1f}x target)"
    
    if distance_ratio < cfg.TARGET_RATIO_MIN:
        return False, f"route too short ({distance_ratio:.1f}x target)"
    
    # Check minimum score
    score = calculate_route_quality(result, target_distance_km)
    if score < cfg.MIN_ACCEPTABLE_SCORE:
        return False, f"quality too low (score {score:.0f})"
    
    return True, ""
