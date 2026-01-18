"""
Shape Service - Route generation from SVG shapes

This is the main entry point for route generation. It handles:
- SVG acquisition from various sources (shape_id, text, image, prompt)
- Calling the unified route generator
- Building the response
"""

import math
from pathlib import Path
import json
from .route_generator import route_with_scaling, route_with_bounds, calculate_approach_distances
from .scoring import calculate_route_quality
from .llm_service import generate_svg_from_prompt
from .text_to_svg import text_to_svg_path_cached
from . import routing_config as cfg
from app.config import settings

SHAPES_PATH = Path(__file__).parent.parent / "data" / "shapes.json"


def load_shapes() -> dict:
    """Load predefined shapes from shapes.json"""
    with open(SHAPES_PATH) as f:
        return json.load(f)


# compute_optimal_aspect_ratio removed - replaced by authoritative bounds


def get_svg_path_and_metadata(
    shape_id: str | None = None,
    prompt: str | None = None,
    text: str | None = None,
    image_svg_path: str | None = None,
    distance_km: float = 5.0
) -> tuple[str, str, str]:
    """
    Get SVG path from any of the supported sources.
    
    Priority: image_svg_path > text > prompt > shape_id
    
    Returns:
        (svg_path, shape_name, shape_id)
    """
    if image_svg_path:
        print(f"🖼️ Image SVG Path: {image_svg_path[:80]}...")
        return image_svg_path, "Custom Image", "image"
    
    if text:
        print(f"📝 Text Input: {text}")
        svg_path = text_to_svg_path_cached(text)
        return svg_path, f"Text: {text}", "text"
    
    if prompt:
        print(f"✨ Custom Prompt: {prompt}")
        svg_path = generate_svg_from_prompt(prompt, distance_km)
        return svg_path, f"Custom: {prompt}", "custom"
    
    if shape_id:
        shapes = load_shapes()
        if shape_id not in shapes:
            raise ValueError(f"Unknown shape: {shape_id}")
        return shapes[shape_id]["svg_path"], shapes[shape_id]["name"], shape_id
    
    raise ValueError("No shape specified")


async def generate_route(
    shape_id: str | None = None,
    start_lat: float = 0,
    start_lng: float = 0,
    distance_km: float = 5.0,
    prompt: str | None = None,
    text: str | None = None,
    image_svg_path: str | None = None,
    aspect_ratio: float = 1.0,
    fast_mode: bool = False
) -> dict:
    """
    Main entry point for route generation.
    
    Uses iterative scaling to find the right size, which is simpler and more
    effective than testing multiple fixed variants.
    
    Args:
        shape_id: Predefined shape ID from shapes.json
        start_lat: Center latitude
        start_lng: Center longitude
        distance_km: Target distance in km
        prompt: LLM prompt for custom shape
        text: Text to convert to SVG (e.g., "NUS", "67")
        image_svg_path: Pre-converted SVG path from uploaded image
        aspect_ratio: Shape stretch factor (>1 = taller)
        fast_mode: If True, use fewer points for faster resize/move
    
    Returns:
        dict with route GeoJSON, distance, score, metadata
    """
    # Get SVG path from appropriate source
    svg_path, shape_name, current_shape_id = get_svg_path_and_metadata(
        shape_id=shape_id,
        prompt=prompt,
        text=text,
        image_svg_path=image_svg_path,
        distance_km=distance_km
    )
    
    # Choose point count based on mode
    num_points = 50 if fast_mode else cfg.POINTS_DEFAULT
    
    print(f"📐 Generating '{current_shape_id}' ({distance_km}km, aspect={aspect_ratio:.2f})")
    
    # Generate route using iterative scaling
    routing_result = await route_with_scaling(
        svg_path=svg_path,
        start_lat=start_lat,
        start_lng=start_lng,
        distance_km=distance_km,
        aspect_ratio=aspect_ratio,
        rotation_deg=0,  # Could add rotation support later if needed
        num_points=num_points
    )
    
    # Extract results
    osrm_result = routing_result["result"]
    route_coords = osrm_result["route"]["coordinates"]
    
    # Calculate approach/return distances
    travel_distances = calculate_approach_distances(start_lat, start_lng, route_coords)
    
    # Build response
    response = {
        # Identity
        "shape_id": current_shape_id,
        "shape_name": shape_name,
        "input_prompt": prompt,
        "svg_path": svg_path,
        
        # Route data
        "route": osrm_result["route"],
        "distance_m": osrm_result["distance_m"],
        "duration_s": osrm_result["duration_s"],
        
        # Quality metrics
        "score": routing_result["score"],
        "scale_factor": routing_result["scale_factor"],
        
        # Travel distances
        "approach_distance_m": travel_distances["approach_distance_m"],
        "return_distance_m": travel_distances["return_distance_m"],
        "total_with_travel_m": round(
            osrm_result["distance_m"] + 
            travel_distances["approach_distance_m"] + 
            travel_distances["return_distance_m"], 1
        ),
        
        # Metadata
        "algorithm": "iterative-scaling",
        "rotation_deg": 0,
        "gps_points": routing_result["gps_points"],
        "original_points": [],  # Not needed in response
        
        # Debug info
        "debug_log": [
            f"scale_factor: {routing_result['scale_factor']:.2f}",
            f"distance_ratio: {routing_result['distance_ratio']:.2f}"
        ]
    }
    
    print(f"🏁 Done: {osrm_result['distance_m']:.0f}m, score={routing_result['score']:.0f}")
    
    return response


async def generate_route_with_bounds(
    shape_id: str | None = None,
    prompt: str | None = None,
    text: str | None = None,
    image_svg_path: str | None = None,
    min_lat: float = 0,
    max_lat: float = 0,
    min_lng: float = 0,
    max_lng: float = 0,
    fast_mode: bool = False
) -> dict:
    """
    Generate a route that fits EXACTLY within the specified GPS bounds.
    
    This is the authoritative bounds function - the bounding box stays exactly
    where the user dragged it. No iterative scaling or aspect ratio adjustment.
    
    Args:
        shape_id: Predefined shape ID from shapes.json
        prompt: LLM prompt for custom shape
        text: Text to convert to SVG (e.g., "NUS", "67")
        image_svg_path: Pre-converted SVG path from uploaded image
        min_lat, max_lat, min_lng, max_lng: Target GPS bounding box
        fast_mode: If True, use fewer points for faster resize/move
    
    Returns:
        dict with route GeoJSON, distance, score, metadata
    """
    # Compute distance from bounds for SVG generation
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    lat_span_km = (max_lat - min_lat) * 111.32
    lng_span_km = (max_lng - min_lng) * 111.32 * math.cos(math.radians(center_lat))
    estimated_perimeter_km = 2 * (lat_span_km + lng_span_km)
    
    # Get SVG path from appropriate source
    svg_path, shape_name, current_shape_id = get_svg_path_and_metadata(
        shape_id=shape_id,
        prompt=prompt,
        text=text,
        image_svg_path=image_svg_path,
        distance_km=estimated_perimeter_km * 1.4  # Rough estimate
    )
    
    # Choose point count based on mode
    num_points = 50 if fast_mode else cfg.POINTS_DEFAULT
    
    print(f"📦 Generating '{current_shape_id}' with bounds")
    
    # Generate route using bounds-based scaling (no iteration!)
    routing_result = await route_with_bounds(
        svg_path=svg_path,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        num_points=num_points
    )
    
    # Extract results
    osrm_result = routing_result["result"]
    route_coords = osrm_result["route"]["coordinates"]
    
    # Calculate approach/return distances from center
    travel_distances = calculate_approach_distances(center_lat, center_lng, route_coords)
    
    # Build response
    response = {
        # Identity
        "shape_id": current_shape_id,
        "shape_name": shape_name,
        "input_prompt": prompt,
        "svg_path": svg_path,
        
        # Route data
        "route": osrm_result["route"],
        "distance_m": osrm_result["distance_m"],
        "duration_s": osrm_result["duration_s"],
        
        # Quality metrics
        "score": routing_result["score"],
        "scale_factor": routing_result["scale_factor"],
        
        # Travel distances
        "approach_distance_m": travel_distances["approach_distance_m"],
        "return_distance_m": travel_distances["return_distance_m"],
        "total_with_travel_m": round(
            osrm_result["distance_m"] + 
            travel_distances["approach_distance_m"] + 
            travel_distances["return_distance_m"], 1
        ),
        
        # Metadata
        "algorithm": "bounds-based",
        "rotation_deg": 0,
        "gps_points": routing_result["gps_points"],
        "original_points": [],
        
        # Bounds metadata
        "bounds": {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
        }
    }
    
    print(f"🏁 Done: {osrm_result['distance_m']:.0f}m, score={routing_result['score']:.0f}")
    
    return response
