import httpx
import json
from app.config import settings

# Mapbox Directions API limit
MAPBOX_MAX_COORDS = 25


async def _call_mapbox_directions(
    gps_points: list[tuple[float, float]],
    profile: str,
    radius: int
) -> dict:
    """
    Single Mapbox Directions API call.
    Returns route geometry, distance, and duration.
    """
    # Format coordinates as "lng,lat;lng,lat;..."
    coords = ";".join([f"{p[1]},{p[0]}" for p in gps_points])
    
    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coords}"
    radiuses_str = ";".join([str(radius)] * len(gps_points))
    
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
        "radiuses": radiuses_str
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=15.0)
        data = response.json()
    
    if response.status_code == 200 and data.get("code") == "Ok":
        route = data["routes"][0]
        return {
            "route": route["geometry"],
            "distance_m": route["distance"]
        }
    
    error_code = data.get("code", "Unknown")
    raise ValueError(f"Mapbox API Error: {error_code}")


async def snap_to_roads(
    gps_points: list[tuple[float, float]],
    profile: str = "walking",
    **kwargs
) -> dict:
    """
    Call Mapbox Directions API to generate a runnable route connecting the points.
    Supports chunked routing for more than 25 points.
    Returns GeoJSON LineString.
    """
    radius = kwargs.get("radius", 200)
    
    # If within limit, single call
    if len(gps_points) <= MAPBOX_MAX_COORDS:
        return await _call_mapbox_directions(gps_points, profile, radius)
    
    # Chunked routing for >25 points
    # Split into overlapping chunks (last point of chunk N = first point of chunk N+1)
    chunks = []
    i = 0
    while i < len(gps_points):
        end = min(i + MAPBOX_MAX_COORDS, len(gps_points))
        chunks.append(gps_points[i:end])
        i = end - 1  # Overlap by 1 point for continuity
        if i >= len(gps_points) - 1:
            break
    
    print(f"   📦 Chunked routing: {len(gps_points)} points -> {len(chunks)} chunks")
    
    # Call Mapbox for each chunk
    all_coords = []
    total_distance = 0.0
    
    for idx, chunk in enumerate(chunks):
        try:
            result = await _call_mapbox_directions(chunk, profile, radius)
            chunk_coords = result["route"]["coordinates"]
            
            # Skip first point of subsequent chunks (it's duplicate from overlap)
            if idx > 0 and chunk_coords:
                chunk_coords = chunk_coords[1:]
            
            all_coords.extend(chunk_coords)
            total_distance += result["distance_m"]
            
        except Exception as e:
            print(f"   ⚠️ Chunk {idx+1} failed: {e}")
            raise
    
    return {
        "route": {"type": "LineString", "coordinates": all_coords},
        "distance_m": total_distance
    }
