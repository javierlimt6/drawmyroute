import httpx
import json
from app.config import settings

async def snap_to_roads(
    gps_points: list[tuple[float, float]],
    profile: str = "walking",
    **kwargs
) -> dict:
    """
    Call Mapbox Directions API to generate a runnable route connecting the points.
    Returns GeoJSON LineString.
    """
    # Format coordinates as "lng,lat;lng,lat;..."
    coords = ";".join([f"{p[1]},{p[0]}" for p in gps_points])
    
    # Use Directions API instead of Matching API
    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coords}"
    
    # Allow snapping to roads based on passed radius (or default to 200m)
    # If using 'unlimited' radius, we can omit the parameter or use 'unlimited' (Mapbox supports 'unlimited' in Matching but Directions uses number)
    # Actually Directions API uses 'radiuses' with numbers or 'unlimited' string? 
    # Let's stick to numbers.
    
    # We will pass 'radiuses' as an argument to this function in the future refactor,
    # but for now let's just use a high default or accept it as kwargs.
    
    # Hack: Let's extract radius from kwargs or default to 200
    radius = kwargs.get("radius", 200)
    radiuses_str = ";".join([str(radius)] * len(gps_points))
    
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
        "radiuses": radiuses_str
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
            
        # If API returns explicit error (e.g. NoRoute), raise it so we can retry
        # with relaxed parameters in the shape_service
        error_code = data.get("code", "Unknown")
        raise ValueError(f"Mapbox API Error: {error_code}")
        
    except Exception as e:
        # Re-raise to let shape_service handle the retry logic
        raise e
