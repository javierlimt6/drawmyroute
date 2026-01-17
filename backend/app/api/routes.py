from fastapi import APIRouter, HTTPException
from app.models.schemas import RouteRequest, RouteResponse
from app.services.shape_service import generate_route, load_shapes

router = APIRouter(prefix="/api/v1")

@router.get("/shapes")
async def list_shapes():
    """List all available predefined shapes."""
    return load_shapes()

@router.post("/generate", response_model=RouteResponse)
async def generate_route_endpoint(request: RouteRequest):
    """Generate a route from a predefined shape."""
    try:
        return await generate_route(
            shape_id=request.shape_id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            distance_km=request.distance_km,
            prompt=request.prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

