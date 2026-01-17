"""
OSRM Point-to-Point Router

Routes between each consecutive pair of GPS points using OSRM.
Each segment is the shortest path, avoiding the cross-back issues of chunked routing.
"""

import httpx
import asyncio
from typing import Optional
from app.config import settings

# Use configured OSRM URL (defaults to local Docker container)
OSRM_BASE_URL = settings.OSRM_URL

# Local server is fast - can handle more concurrent requests
MAX_CONCURRENT = 20
BATCH_DELAY_MS = 0  # No delay needed for local server


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
    Route through all GPS points using OSRM point-to-point routing.
    Each segment is routed separately for cleaner paths.
    Uses batching to avoid rate limiting.
    
    Args:
        gps_points: List of (lat, lng) tuples
        profile: 'foot', 'bike', or 'car'
    
    Returns:
        dict with 'route' (GeoJSON LineString), 'distance_m', 'duration_s'
    """
    if len(gps_points) < 2:
        raise ValueError("Need at least 2 points for routing")
    
    num_segments = len(gps_points) - 1
    print(f"   🛤️ OSRM point-to-point: {len(gps_points)} points -> {num_segments} segments")
    
    # Create segment pairs
    segments = [(gps_points[i], gps_points[i + 1]) for i in range(num_segments)]
    
    # Process in batches to avoid rate limiting
    results = []
    async with httpx.AsyncClient() as client:
        for batch_start in range(0, len(segments), MAX_CONCURRENT):
            batch = segments[batch_start:batch_start + MAX_CONCURRENT]
            
            # Route batch in parallel
            tasks = [route_segment_osrm(start, end, profile, client) for start, end in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Small delay between batches
            if batch_start + MAX_CONCURRENT < len(segments):
                await asyncio.sleep(BATCH_DELAY_MS / 1000.0)
    
    # Combine all segment results
    all_coords = []
    total_distance = 0.0
    total_duration = 0.0
    failed_segments = 0
    
    for i, result in enumerate(results):
        if result:
            segment_coords = result["coordinates"]
            # Skip first point of subsequent segments (it's duplicate)
            if i > 0 and segment_coords:
                segment_coords = segment_coords[1:]
            
            all_coords.extend(segment_coords)
            total_distance += result["distance_m"]
            total_duration += result["duration_s"]
        else:
            failed_segments += 1
            # Fallback: add straight line between points
            start, end = segments[i]
            if i == 0:
                all_coords.append([start[1], start[0]])
            all_coords.append([end[1], end[0]])
    
    if failed_segments > 0:
        print(f"   ⚠️ {failed_segments}/{num_segments} segments failed, used straight lines")
    else:
        print(f"   ✅ All {num_segments} segments routed successfully")
    
    if not all_coords:
        raise ValueError("OSRM routing failed for all segments")
    
    return {
        "route": {"type": "LineString", "coordinates": all_coords},
        "distance_m": total_distance,
        "duration_s": total_duration,
        "failed_segments": failed_segments,
        "total_segments": num_segments
    }
