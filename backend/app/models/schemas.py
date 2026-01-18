from pydantic import BaseModel, model_validator
from typing import Optional

class RouteRequest(BaseModel):
    shape_id: Optional[str] = None
    prompt: Optional[str] = None
    text: Optional[str] = None  # Text to convert to route shape (e.g., "NUS", "67")
    image_svg_path: Optional[str] = None  # SVG path from uploaded image
    start_lat: float
    start_lng: float
    distance_km: float
    aspect_ratio: float = 1.0  # >1 = taller, <1 = wider (range: 0.25-4.0)
    fast_mode: bool = False     # Skip multi-variant optimization for faster resize
    adaptive_resize: bool = False  # Enable adaptive height calculation for width changes
    width_ratio: Optional[float] = None  # How much width changed (>1 = wider)

    @model_validator(mode='after')
    def check_shape_source(self):
        if not self.shape_id and not self.prompt and not self.text and not self.image_svg_path:
            raise ValueError("Either shape_id, prompt, text, or image_svg_path must be provided")
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
    rotation_deg: float = 0
    duration_s: float


class SuggestRequest(BaseModel):
    """Request schema for auto-suggest route endpoint."""
    start_lat: float
    start_lng: float
    distance_km: float
    num_candidates: int = 10  # How many shapes to try
    aspect_ratio: float = 1.0
