import os
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Setup Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "app" / "data"
LUCIDE_DIR = SCRIPT_DIR / "lucide"
ICONS_DIR = LUCIDE_DIR / "icons"

def run_extraction():
    # 1. Clone Lucide if not exists
    if not LUCIDE_DIR.exists():
        print("⬇️  Cloning Lucide icons...")
        try:
            subprocess.run(["git", "clone", "--depth", "1", "https://github.com/lucide-icons/lucide.git", str(LUCIDE_DIR)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone failed: {e}")
            return

    data_store = {}      # { "icon_name": "M12 9c..." }
    semantic_index = []  # [ {"name": "dog", "tags": ["animal", "pet"]}, ... ]

    print("⚙️  Processing icons...")
    
    if not ICONS_DIR.exists():
        print(f"❌ Icons directory not found at {ICONS_DIR}")
        return

    count = 0
    for filename in os.listdir(ICONS_DIR):
        if filename.endswith(".svg"):
            name = filename.replace(".svg", "")
            
            try:
                # 1. Extract SVG Path
                tree = ET.parse(ICONS_DIR / filename)
                root = tree.getroot()
                # Lucide paths use the SVG namespace
                ns = {'svg': 'http://www.w3.org/2000/svg'}
                
                # Extract 'd' from all path elements
                paths = [p.attrib['d'] for p in root.findall(".//svg:path", ns) if 'd' in p.attrib]
                
                # Fallback: check without namespace
                if not paths:
                     paths = [p.attrib['d'] for p in root.findall(".//path") if 'd' in p.attrib]

                if not paths:
                    continue

                full_d = " ".join(paths)
                data_store[name] = full_d
                
                # 2. Extract Characteristics (Tags)
                json_path = ICONS_DIR / f"{name}.json"
                tags = []
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        meta = json.load(f)
                        tags = meta.get("tags", [])
                
                semantic_index.append({"name": name, "tags": tags})
                count += 1
            except Exception as e:
                # print(f"Skipping {name}: {e}")
                pass

    # Save the files
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_DIR / "data_store.json", "w") as f:
        json.dump(data_store, f)
    with open(DATA_DIR / "semantic_index.json", "w") as f:
        json.dump(semantic_index, f)
    
    print(f"✅ Processed {count} icons.")
    print(f"📂 Saved to {DATA_DIR}")

if __name__ == "__main__":
    run_extraction()
