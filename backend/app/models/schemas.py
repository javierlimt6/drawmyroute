from pydantic import BaseModel

class RouteRequest(BaseModel):
    shape_id: str
    start_lat: float
    start_lng: float
    distance_km: float

class RouteResponse(BaseModel):
    shape_id: str
    shape_name: str
    original_points: list[tuple[float, float]]
    gps_points: list[tuple[float, float]]
    route: dict  # GeoJSON LineString
    distance_m: float
    duration_s: float
