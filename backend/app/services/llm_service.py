import json
import os
from pathlib import Path
from openai import OpenAI
import cv2
import numpy as np
import httpx
from app.config import settings
from app.utils.embeddings import search_vector_index

CACHE_PATH = Path(__file__).parent.parent / "data" / "prompt_cache.json"
DATA_DIR = Path(__file__).parent.parent / "data"
SEMANTIC_INDEX_PATH = DATA_DIR / "semantic_index.json"
DATA_STORE_PATH = DATA_DIR / "data_store.json"

# Load Assets on Startup
SEMANTIC_INDEX = []
DATA_STORE = {}

try:
    if SEMANTIC_INDEX_PATH.exists():
        with open(SEMANTIC_INDEX_PATH) as f:
            SEMANTIC_INDEX = json.load(f)
    if DATA_STORE_PATH.exists():
        with open(DATA_STORE_PATH) as f:
            DATA_STORE = json.load(f)
except Exception as e:
    print(f"⚠️ Failed to load icon assets: {e}")

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
    """Convert list of [x,y] to SVG path string."""
    if not points: return ""
    d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for p in points[1:]:
        d += f" L {p[0]:.1f} {p[1]:.1f}"
    d += " Z"
    return d

def _trace_image_to_svg(image_url: str) -> str:
    """Download image, trace largest contour, simplify, normalize."""
    resp = httpx.get(image_url)
    resp.raise_for_status()
    image_bytes = np.asarray(bytearray(resp.content), dtype="uint8")
    img = cv2.imdecode(image_bytes, cv2.IMREAD_GRAYSCALE)
    if img is None: raise ValueError("Failed to decode image")

    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours: raise ValueError("No shape detected")
        
    largest_cnt = max(contours, key=cv2.contourArea)
    epsilon = 0.015 * cv2.arcLength(largest_cnt, True)
    approx = cv2.approxPolyDP(largest_cnt, epsilon, True)
    
    if len(approx) < 3: raise ValueError("Shape too simple")
        
    points = approx.reshape(-1, 2).astype(float)
    min_vals = np.min(points, axis=0)
    max_vals = np.max(points, axis=0)
    ranges = max_vals - min_vals
    ranges[ranges == 0] = 1 
    
    normalized = (points - min_vals) / ranges * 100
    return points_to_svg(normalized.tolist())

def _get_best_icon_match(prompt: str) -> str | None:
    """Two-Stage Retrieval: Vector Search + LLM Re-Ranking."""
    if not SEMANTIC_INDEX:
        return None
        
    # 1. Broad Search (Vector Index)
    top_indices = search_vector_index(prompt, top_k=15)
    
    if not top_indices:
        print(f"⚠️ Vector search found no candidates for '{prompt}'")
        # Fallback to DALL-E directly? Or return None to let caller handle fallback.
        return None
        
    candidates = [SEMANTIC_INDEX[i] for i in top_indices]
    
    # 2. Narrow Re-Ranking (LLM)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    candidate_context = "\n".join([f"- {c['name']} (Tags: {', '.join(c.get('tags', []))})" for c in candidates])
    
    sys_prompt = f"""
    Pick the BEST icon name from the list below for the user query.
    
    Rules:
    1. ONLY return the exact name. No markdown, no quotes.
    2. If no reasonable match exists, return 'NONE'.
    3. Prefer exact semantic matches (e.g. "dog" for "pup").
    
    Candidates:
    {candidate_context}
    """
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        raw_match = resp.choices[0].message.content.strip()
        
        # Robust cleanup
        match = raw_match.replace("'", "").replace('"', "").replace("`", "").strip().lower()
        
        print(f"🤖 Retrieval Debug: Prompt='{prompt}' -> Candidates={len(candidates)} -> Selected='{match}'")
        
        if match != "none" and match in DATA_STORE:
            return match
            
        return None
    except Exception as e:
        print(f"⚠️ Retrieval failed: {e}")
        return None

def _generate_with_dalle(prompt: str) -> str:
    """Fallback: Generate with DALL-E 2."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Use DALL-E 2 for speed/cost as discussed
    dalle_prompt = (
        f"A simple, flat black silhouette of a {prompt} on a pure white background. "
        "High contrast, vector icon style. No fine details. Single closed shape."
    )
    
    response = client.images.generate(
        model="dall-e-2",
        prompt=dalle_prompt,
        size="256x256",
        n=1,
    )
    
    image_url = response.data[0].url
    if not image_url:
        raise ValueError("No image URL returned")
        
    print(f"🖼️ Tracing Image...")
    return _trace_image_to_svg(image_url)

def generate_svg_from_prompt(prompt: str, distance_km: float = 5.0) -> str:
    """
    Hybrid Generation: Retrieval First -> DALL-E Fallback.
    """
    # 1. Check Cache
    cache = _load_cache()
    cache_key = f"{prompt.lower().strip()}_hybrid"
    if cache_key in cache:
        print(f"🧠 Cache Hit for '{prompt}'")
        return cache[cache_key]

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    # 2. Try Retrieval
    print(f"🔍 Searching icon library for '{prompt}'...")
    icon_name = _get_best_icon_match(prompt)
    
    if icon_name:
        print(f"🎯 Found Icon Match: '{icon_name}'")
        svg_d = DATA_STORE[icon_name]
        
        # Ensure closure
        if "z" not in svg_d.lower():
            svg_d += " Z"
            
        # Cache & Return
        cache[cache_key] = svg_d
        _save_cache(cache)
        return svg_d
        
    # 3. Fallback to DALL-E
    print(f"🎨 No match found. Generating with DALL-E...")
    try:
        final_d = _generate_with_dalle(prompt)
        cache[cache_key] = final_d
        _save_cache(cache)
        return final_d
    except Exception as e:
        print(f"Generation Failed: {e}")
        raise ValueError(f"Failed to generate shape: {str(e)}")
