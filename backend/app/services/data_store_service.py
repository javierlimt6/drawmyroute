"""
Data Store Service - Loads and samples SVG paths from data_store.json
"""
import json
import random
from pathlib import Path

DATA_STORE_PATH = Path(__file__).parent.parent / "data" / "data_store.json"
MATERIAL_STORE_PATH = Path(__file__).parent.parent / "data" / "material_store.json"

_data_store_cache: dict | None = None


def load_data_store() -> dict:
    """Load and merge all SVG paths from data stores."""
    global _data_store_cache
    if _data_store_cache is None:
        # Load main store (Lucide + Presets)
        with open(DATA_STORE_PATH) as f:
            main_store = json.load(f)
            
        # Load material store (Google Material Icons)
        material_store = {}
        if MATERIAL_STORE_PATH.exists():
            try:
                with open(MATERIAL_STORE_PATH) as f:
                    material_store = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load material_store.json: {e}")
        
        # Merge: Main store takes precedence for name collisions
        _data_store_cache = {**material_store, **main_store}
        print(f"📚 Data Store Loaded: {len(_data_store_cache)} icons (Main: {len(main_store)}, Material: {len(material_store)})")
        
    return _data_store_cache


def is_continuous_path(svg_path: str) -> bool:
    """
    Check if an SVG path is continuous (suitable for route generation).
    
    A continuous path should have only ONE 'M' or 'm' command at the start,
    meaning it's a single connected shape rather than multiple disconnected strokes.
    """
    # Count moveto commands (M or m) - case insensitive
    # A continuous path should only have 1 moveto at the start
    path_upper = svg_path.upper()
    m_count = path_upper.count(' M') + path_upper.count('\tM')
    
    # If it starts with M, that's the first one (not preceded by space)
    if path_upper.startswith('M'):
        m_count += 1
    
    # Also count lowercase 'm' that aren't at the very start (relative moveto mid-path)
    m_count += svg_path.count(' m') + svg_path.count('\tm')
    
    # A good continuous path has exactly 1 M command (at the start)
    # and ideally ends with Z (closed path)
    return m_count <= 1


def get_random_shapes(num_shapes: int = 10) -> list[tuple[str, str]]:
    """
    Get random (name, svg_path) tuples from the data store.
    ONLY returns shapes with continuous paths (single M command).
    
    Args:
        num_shapes: Number of random shapes to return
        
    Returns:
        List of (shape_name, svg_path) tuples
    """
    data = load_data_store()
    
    # Filter for continuous paths only
    continuous_items = [
        (name, path) for name, path in data.items()
        if is_continuous_path(path)
    ]
    
    print(f"📊 [DataStore] {len(continuous_items)}/{len(data)} shapes are continuous paths")
    
    return random.sample(continuous_items, min(num_shapes, len(continuous_items)))


def get_all_shape_names() -> list[str]:
    """Get all available shape names."""
    return list(load_data_store().keys())


def get_shape_by_name(name: str) -> str | None:
    """Get a specific shape's SVG path by name."""
    return load_data_store().get(name)
