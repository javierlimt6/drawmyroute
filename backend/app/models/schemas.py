from pydantic import BaseModel, model_validator
from typing import Optional

class RouteRequest(BaseModel):
    shape_id: Optional[str] = None
    prompt: Optional[str] = None
    start_lat: float
    start_lng: float
    distance_km: float
    aspect_ratio: float = 1.0  # >1 = taller, <1 = wider (range: 0.25-4.0)
    fast_mode: bool = False     # Skip multi-variant optimization for faster resize

    @model_validator(mode='after')
    def check_shape_source(self):
        if not self.shape_id and not self.prompt:
            raise ValueError("Either shape_id or prompt must be provided")
        # Clamp aspect_ratio to reasonable range
        self.aspect_ratio = max(0.25, min(4.0, self.aspect_ratio))
        return self

class RouteResponse(BaseModel):
    shape_id: str
    shape_name: str
    input_prompt: Optional[str] = None
    svg_path: str
    original_points: list[tuple[float, float]]
    gps_points: list[tuple[float, float]]
    route: dict  # GeoJSON LineString
    distance_m: float
