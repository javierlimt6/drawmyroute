from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.models.schemas import RouteRequest, RouteResponse
from app.services.shape_service import generate_route, load_shapes
from app.services.gpx_exporter import generate_gpx, get_gpx_filename

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
            prompt=request.prompt,
            text=request.text,
            aspect_ratio=request.aspect_ratio,
            fast_mode=request.fast_mode
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/gpx")
async def export_gpx(request: RouteRequest):
    """Generate a route and export it as a downloadable GPX file."""
    try:
        # Generate the route first
        result = await generate_route(
            shape_id=request.shape_id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            distance_km=request.distance_km,
            prompt=request.prompt,
            text=request.text,
            aspect_ratio=request.aspect_ratio
        )
        
        # Convert to GPX
        gpx_content = generate_gpx(
            route_geojson=result["route"],
            name=result["shape_name"],
            distance_m=result["distance_m"],
            duration_s=result["duration_s"]
        )
        
        # Generate filename
        filename = get_gpx_filename(result["shape_name"], result["distance_m"])
        
        return Response(
            content=gpx_content,
            media_type="application/gpx+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

