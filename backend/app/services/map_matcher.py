import httpx
import json
from app.config import settings

async def snap_to_roads(
    gps_points: list[tuple[float, float]],
    profile: str = "walking"
) -> dict:
    """
    Call Mapbox Directions API to generate a runnable route connecting the points.
    Returns GeoJSON LineString.
    """
    # Format coordinates as "lng,lat;lng,lat;..."
    coords = ";".join([f"{p[1]},{p[0]}" for p in gps_points])
    
    # Use Directions API instead of Matching API
    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coords}"
    
    # Allow snapping to roads within 200 meters of each waypoint
    # We need one radius per coordinate
    radiuses = ";".join(["200"] * len(gps_points))
    
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
        "radiuses": radiuses 
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            data = response.json()
        
        if response.status_code == 200 and data.get("code") == "Ok":
            route = data["routes"][0]
            return {
                "route": route["geometry"],
                "distance_m": route["distance"],
                "duration_s": route["duration"]
            }
            
        # Enhanced Debugging
        print(f"\n⚠️ Mapbox API Failed!")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        print(f"Request URL: {url}")
        
    except Exception as e:
        print(f"Map Matching Error: {e}")

    # Fallback: Return straight lines (GeoJSON)
    return {
        "route": {
            "type": "LineString",
            "coordinates": [[p[1], p[0]] for p in gps_points]
        },
        "distance_m": 0, 
        "duration_s": 0
    }
