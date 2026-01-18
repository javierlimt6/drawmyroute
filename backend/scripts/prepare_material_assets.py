
import json
import httpx
from pathlib import Path
import sys

# Setup Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "app" / "data"

# Add backend to path to import app and prepare_assets
sys.path.append(str(ROOT_DIR))
sys.path.append(str(SCRIPT_DIR))

try:
    from prepare_assets import normalize_svg_path
    from app.utils.embeddings import build_vector_index
except ImportError as e:
    print(f"❌ Failed to import dependencies: {e}")
    sys.exit(1)

def run_material_extraction():
    url = "https://raw.githubusercontent.com/livingdocsIO/material-design-icons-svg/master/paths.json"
    print(f"⬇️  Downloading Material Icons from {url}...")
    
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return

    material_store = {}
    semantic_index_updates = []
    
    print(f"⚙️  Processing {len(data)} icons...")
    
    count = 0
    for name, path in data.items():
        # Material icons might have multiple paths or extra whitespace
        # The source JSON seems to have simple path strings.
        
        norm_d = normalize_svg_path(path)
        
        if norm_d:
            material_store[name] = norm_d
            semantic_index_updates.append({
                "name": name,
                "tags": [name.replace("-", " "), "material", "icon"]
            })
            count += 1
            if count % 500 == 0:
                print(f"   Processed {count}...")
        
    print(f"✅ Normalized {len(material_store)} material icons.")

    # Save material_store.json
    MATERIAL_STORE_PATH = DATA_DIR / "material_store.json"
    with open(MATERIAL_STORE_PATH, "w") as f:
        json.dump(material_store, f)
    print(f"📂 Saved material store to {MATERIAL_STORE_PATH}")

    # Update Semantic Index
    SEMANTIC_INDEX_PATH = DATA_DIR / "semantic_index.json"
    existing_index = []
    if SEMANTIC_INDEX_PATH.exists():
        with open(SEMANTIC_INDEX_PATH, "r") as f:
            existing_index = json.load(f)
    
    # Merge (avoid duplicates by name)
    existing_names = {item["name"] for item in existing_index}
    new_entries = [item for item in semantic_index_updates if item["name"] not in existing_names]
    
    combined_index = existing_index + new_entries
    
    with open(SEMANTIC_INDEX_PATH, "w") as f:
        json.dump(combined_index, f)
    
    print(f"🧠 Updated semantic index with {len(new_entries)} new entries.")
    
    # Rebuild Vector Index
    print("🧠 Rebuilding Vector Index...")
    build_vector_index(combined_index)

if __name__ == "__main__":
    run_material_extraction()
