from pydantic import BaseModel, model_validator
from typing import Optional

class RouteRequest(BaseModel):
    shape_id: Optional[str] = None
    prompt: Optional[str] = None
    start_lat: float
    start_lng: float
    distance_km: float

    @model_validator(mode='after')
    def check_shape_source(self):
        if not self.shape_id and not self.prompt:
            raise ValueError("Either shape_id or prompt must be provided")
        return self

class RouteResponse(BaseModel):
    shape_id: str
    shape_name: str
    svg_path: str
    original_points: list[tuple[float, float]]
    gps_points: list[tuple[float, float]]
    route: dict  # GeoJSON LineString
    distance_m: float
    duration_s: float
