from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from app.models.schemas import RouteRequest, RouteResponse, SuggestRequest
from app.services.shape_service import generate_route, load_shapes, compute_optimal_aspect_ratio
from app.services.gpx_exporter import generate_gpx, get_gpx_filename
from app.services.image_to_svg import image_to_svg_path
from app.services.suggest_service import suggest_best_route

router = APIRouter(prefix="/api/v1")


@router.post("/parse-image")
async def parse_image(file: UploadFile = File(...)):
    """Parse an uploaded image and extract SVG path for route generation."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (PNG, JPG, etc.)")
    
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        if len(file_bytes) < 100:
            raise HTTPException(status_code=400, detail="File is too small or empty")
        
        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File is too large (max 10MB)")
        
        # Convert to SVG path
        svg_path = image_to_svg_path(file_bytes)
        
        return {"svg_path": svg_path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@router.get("/shapes")
async def list_shapes():
    """List all available predefined shapes."""
    return load_shapes()

@router.post("/generate", response_model=RouteResponse)
async def generate_route_endpoint(request: RouteRequest):
    """Generate a route from a predefined shape."""
    try:
        # Handle adaptive resize: compute optimal aspect ratio from width change
        aspect_ratio = request.aspect_ratio
        if request.adaptive_resize and request.width_ratio:
            aspect_ratio = compute_optimal_aspect_ratio(
                current_aspect=request.aspect_ratio,
                width_ratio=request.width_ratio
            )
            print(f"📐 Adaptive resize: width_ratio={request.width_ratio:.2f} -> aspect_ratio={aspect_ratio:.2f}")
        
        return await generate_route(
            shape_id=request.shape_id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            distance_km=request.distance_km,
            prompt=request.prompt,
            text=request.text,
            image_svg_path=request.image_svg_path,
            aspect_ratio=aspect_ratio,
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
            image_svg_path=request.image_svg_path,
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


@router.post("/suggest")
async def suggest_route(request: SuggestRequest):
    """Auto-suggest the best route from the shape database for the given location and distance."""
    try:
        return await suggest_best_route(
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            distance_km=request.distance_km,
            num_candidates=request.num_candidates,
            aspect_ratio=request.aspect_ratio
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
