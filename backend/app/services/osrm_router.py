"""
OSRM Point-to-Point Router

Routes between each consecutive pair of GPS points using OSRM.
Each segment is the shortest path, avoiding the cross-back issues of chunked routing.

Includes flexible waypoint routing: detects segments with anomalously high detour
ratios and skips problematic waypoints to improve success rates near parks/water.
"""

import httpx
import asyncio
import math
from typing import Optional
from app.config import settings
from . import routing_config as cfg

# Use configured OSRM URL (defaults to local Docker container)
OSRM_BASE_URL = settings.OSRM_URL

# Use centralized config
MAX_CONCURRENT = cfg.OSRM_MAX_CONCURRENT
DETOUR_THRESHOLD = cfg.DETOUR_THRESHOLD
MAX_SKIP_RATIO = cfg.MAX_SKIP_RATIO
MIN_STRAIGHT_LINE_M = 10  # Minimum straight-line distance to consider


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the straight-line distance between two GPS points in meters.
    Uses the Haversine formula for accuracy on Earth's surface.
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


async def route_segment_osrm(
    start: tuple[float, float],  # (lat, lng)
    end: tuple[float, float],    # (lat, lng)
    profile: str = "foot",
    client: httpx.AsyncClient = None
) -> Optional[dict]:
    """
    Route between two points using OSRM.
    
    Args:
        start: (lat, lng) tuple
        end: (lat, lng) tuple
        profile: 'foot', 'bike', or 'car'
        client: Reusable HTTP client
    
    Returns:
        dict with 'coordinates', 'distance_m', 'duration_s' or None if failed
    """
    # OSRM expects lng,lat order
    coords = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"{OSRM_BASE_URL}/route/v1/{profile}/{coords}"
    
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }
    
    try:
        if client:
            response = await client.get(url, params=params, timeout=10.0)
        else:
            async with httpx.AsyncClient() as c:
                response = await c.get(url, params=params, timeout=10.0)
        
        # Check for rate limiting (empty response or 429)
        if response.status_code == 429:
            print(f"   ⚠️ OSRM rate limited, waiting...")
            await asyncio.sleep(1.0)
            return None
        
        if not response.text:
            return None
            
        data = response.json()
        
        if response.status_code == 200 and data.get("code") == "Ok":
            route = data["routes"][0]
            return {
                "coordinates": route["geometry"]["coordinates"],
                "distance_m": route["distance"],
                "duration_s": route["duration"]
            }
        return None
        
    except Exception as e:
        # Only print if it's not a JSON decode error (which means empty response)
        if "Expecting value" not in str(e):
            print(f"   ⚠️ OSRM segment failed: {e}")
        return None


async def snap_to_roads_osrm(
    gps_points: list[tuple[float, float]],
    profile: str = "foot",
    **kwargs
) -> dict:
    """
    Route through GPS points using OSRM with flexible waypoint routing.
    
    Detects segments with anomalously high detour ratios (road distance >> straight-line)
    and skips problematic waypoints to improve success rates near parks/water.
    
    Args:
        gps_points: List of (lat, lng) tuples
        profile: 'foot', 'bike', or 'car'
    
    Returns:
        dict with 'route', 'distance_m', 'duration_s', 'skipped_points', etc.
    """
    if len(gps_points) < 2:
        raise ValueError("Need at least 2 points for routing")
    
    original_num_points = len(gps_points)
    max_skips_allowed = int(original_num_points * MAX_SKIP_RATIO)
    
    print(f"   🛤️ OSRM flexible routing: {len(gps_points)} points (max {max_skips_allowed} skips)")
    
    # ===== PHASE 1: Initial routing =====
    # Create segment pairs
    segments = [(gps_points[i], gps_points[i + 1]) for i in range(len(gps_points) - 1)]
    
    # Route all segments in parallel
    results = []
    async with httpx.AsyncClient() as client:
        for batch_start in range(0, len(segments), MAX_CONCURRENT):
            batch = segments[batch_start:batch_start + MAX_CONCURRENT]
            tasks = [route_segment_osrm(start, end, profile, client) for start, end in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
    
    # ===== PHASE 2: Detect outliers and plan skips =====
    outlier_indices = []  # Indices of waypoints to potentially skip
    max_detour_ratio = 1.0
    
    for i, (result, (start, end)) in enumerate(zip(results, segments)):
        if result is None:
            continue
            
        # Calculate straight-line distance
        straight_m = haversine_distance_m(start[0], start[1], end[0], end[1])
        straight_m = max(straight_m, MIN_STRAIGHT_LINE_M)  # Avoid tiny denominators
        
        routed_m = result["distance_m"]
        detour_ratio = routed_m / straight_m
        max_detour_ratio = max(max_detour_ratio, detour_ratio)
        
        if detour_ratio > DETOUR_THRESHOLD:
            # The END point of this segment (i+1 in gps_points) is likely problematic
            # Skip it unless it's the first or last point
            if 0 < i + 1 < len(gps_points) - 1:
                outlier_indices.append(i + 1)
                print(f"      ⚠️ Segment {i} outlier: {detour_ratio:.1f}× detour ({straight_m:.0f}m → {routed_m:.0f}m)")
    
    # ===== PHASE 3: Apply skips =====
    skipped_points = 0
    
    if outlier_indices and len(outlier_indices) <= max_skips_allowed:
        # Remove outlier waypoints and re-route affected segments
        skipped_points = len(outlier_indices)
        print(f"      🔧 Skipping {skipped_points} problematic points: {outlier_indices}")
        
        # Create new point list without outliers
        filtered_points = [p for i, p in enumerate(gps_points) if i not in outlier_indices]
        
        # Re-route with filtered points
        new_segments = [(filtered_points[i], filtered_points[i + 1]) for i in range(len(filtered_points) - 1)]
        
        results = []
        async with httpx.AsyncClient() as client:
            for batch_start in range(0, len(new_segments), MAX_CONCURRENT):
                batch = new_segments[batch_start:batch_start + MAX_CONCURRENT]
                tasks = [route_segment_osrm(start, end, profile, client) for start, end in batch]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
        
        segments = new_segments
    elif len(outlier_indices) > max_skips_allowed:
        print(f"      ❌ Too many outliers ({len(outlier_indices)} > {max_skips_allowed}), keeping original")
    
    # ===== PHASE 4: Combine results =====
    all_coords = []
    total_distance = 0.0
    total_duration = 0.0
    failed_segments = 0
    
    for i, result in enumerate(results):
        if result:
            segment_coords = result["coordinates"]
            # Skip first point of subsequent segments (duplicate)
            if i > 0 and segment_coords:
                segment_coords = segment_coords[1:]
            
            all_coords.extend(segment_coords)
            total_distance += result["distance_m"]
            total_duration += result["duration_s"]
        else:
            failed_segments += 1
            # Fallback: straight line
            start, end = segments[i]
            if i == 0:
                all_coords.append([start[1], start[0]])
            all_coords.append([end[1], end[0]])
    
    # ===== Summary logging =====
    num_segments = len(segments)
    if skipped_points > 0:
        print(f"   ✅ Routed with {skipped_points} skips ({skipped_points/original_num_points*100:.0f}%), max detour: {max_detour_ratio:.1f}×")
    elif failed_segments > 0:
        print(f"   ⚠️ {failed_segments}/{num_segments} segments failed, used straight lines")
    else:
        print(f"   ✅ All {num_segments} segments routed (max detour: {max_detour_ratio:.1f}×)")
    
    if not all_coords:
        raise ValueError("OSRM routing failed for all segments")
    
    return {
        "route": {"type": "LineString", "coordinates": all_coords},
        "distance_m": total_distance,
        "duration_s": total_duration,
        "failed_segments": failed_segments,
        "total_segments": num_segments,
        "skipped_points": skipped_points,
        "max_detour_ratio": round(max_detour_ratio, 2)
    }
