import json
import os
from pathlib import Path
from openai import OpenAI
import cv2
import numpy as np
import httpx
from app.config import settings

CACHE_PATH = Path(__file__).parent.parent / "data" / "prompt_cache.json"

def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def _save_cache(cache: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

def points_to_svg(points: list[list[float]]) -> str:
    """
    Convert a list of [x, y] coordinates to a closed SVG path string.
    """
    if not points:
        return ""
    
    d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for p in points[1:]:
        d += f" L {p[0]:.1f} {p[1]:.1f}"
    d += " Z"
    return d

def _trace_image_to_svg(image_url: str) -> str:
    """
    Download image, threshold, find largest contour, simplify, and normalize.
    """
    # 1. Download
    resp = httpx.get(image_url)
    resp.raise_for_status()
    # Convert string buffer to numpy array
    image_bytes = np.asarray(bytearray(resp.content), dtype="uint8")
    img = cv2.imdecode(image_bytes, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Failed to decode image from DALL-E")

    # 2. Threshold (Invert: We want shape to be White on Black for findContours)
    # DALL-E gives Black shape on White background.
    # THRESH_BINARY_INV turns Black(0) to White(255)
    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    
    # 3. Find Contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        raise ValueError("No shape detected in the generated image")
        
    # 4. Pick Largest Contour (The Icon)
    largest_cnt = max(contours, key=cv2.contourArea)
    
    # 5. Simplify (Ramer-Douglas-Peucker)
    # epsilon is max error distance. 1.5% of arc length is a good balance for icons.
    epsilon = 0.015 * cv2.arcLength(largest_cnt, True)
    approx = cv2.approxPolyDP(largest_cnt, epsilon, True)
    
    if len(approx) < 3:
        raise ValueError("Shape is too simple (not enough points)")
        
    # 6. Normalize to 0-100
    points = approx.reshape(-1, 2).astype(float) # (N, 2)
    
    min_vals = np.min(points, axis=0)
    max_vals = np.max(points, axis=0)
    ranges = max_vals - min_vals
    
    # Avoid division by zero
    ranges[ranges == 0] = 1 
    
    # Scale to 0-100
    normalized = (points - min_vals) / ranges * 100
    
    return points_to_svg(normalized.tolist())

def generate_svg_from_prompt(prompt: str, distance_km: float = 5.0) -> str:
    """
    Generate an SVG path from a text prompt using DALL-E 2 + OpenCV Tracing.
    """
    # 1. Check Cache
    cache = _load_cache()
    # New cache key for Image-based generation
    cache_key = f"{prompt.lower().strip()}_r2v"
    if cache_key in cache:
        print(f"🧠 Cache Hit for '{prompt}'")
        return cache[cache_key]

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Cannot generate shape.")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    print(f"🎨 Generating Image for '{prompt}' with DALL-E 2...")
    
    try:
        # 2. Generate Image
        # Optimized prompt for DALL-E 3 to get a tracer-friendly output
        dalle_prompt = (
            f"A single, solid black minimalist silhouette of a {prompt}. "
            "Pure white background. No shading, no gradients, no textures, no gray areas. "
            "One continuous thick black shape. High-contrast vector style."
        )
        
        response = client.images.generate(
            model="dall-e-3", # Upgrade here
            prompt=dalle_prompt,
            size="1024x1024",  # DALL-E 3 size
            quality="standard", # This is valid for DALL-E 3
            n=1,
        )
        
        image_url = response.data[0].url
        if not image_url:
            raise ValueError("No image URL returned")
            
        print(f"🖼️ Tracing Image...")
        
        # 3. Trace to SVG
        final_d = _trace_image_to_svg(image_url)
        
        # 4. Save to Cache
        cache[cache_key] = final_d
        _save_cache(cache)
        
        return final_d
        
    except Exception as e:
        print(f"Generation Failed: {e}")
        raise ValueError(f"Failed to generate shape: {str(e)}")
