import httpx
import json
from app.config import settings

async def snap_to_roads(
    gps_points: list[tuple[float, float]],
    profile: str = "walking"
) -> dict:
    """
    Call Mapbox Map Matching API to snap points to roads.
    Returns GeoJSON LineString.
    Falls back to straight lines if matching fails.
    """
    # Format coordinates as "lng,lat;lng,lat;..."
    coords = ";".join([f"{p[1]},{p[0]}" for p in gps_points])
    
    url = f"https://api.mapbox.com/matching/v5/mapbox/{profile}/{coords}"
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
        "tidy": "true" # Clean up traces
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()
        
        if response.status_code == 200 and data.get("code") == "Ok":
            matching = data["matchings"][0]
            return {
                "route": matching["geometry"],
                "distance_m": matching["distance"],
                "duration_s": matching["duration"]
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
        "distance_m": 0, # Could calculate Euclidean but 0 indicates "estimated"
        "duration_s": 0
    }
