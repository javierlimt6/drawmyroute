import os
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
from svg.path import parse_path, Move, Line, CubicBezier, QuadraticBezier, Arc

# Setup Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "app" / "data"

# Add backend to path to import app
sys.path.append(str(ROOT_DIR))
from app.utils.embeddings import build_vector_index
LUCIDE_DIR = SCRIPT_DIR / "lucide"
ICONS_DIR = LUCIDE_DIR / "icons"

def get_points_from_path(path):
    points = []
    for segment in path:
        if isinstance(segment, (Line, Move)):
            points.append((segment.start.real, segment.start.imag))
            points.append((segment.end.real, segment.end.imag))
        elif isinstance(segment, (CubicBezier, QuadraticBezier, Arc)):
            for t in [i/10 for i in range(11)]:
                pt = segment.point(t)
                points.append((pt.real, pt.imag))
    return points

def normalize_points(points):
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    if not xs or not ys: return points
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    def norm(x, min_, max_): return ((x - min_) / (max_ - min_)) * 100 if max_ > min_ else 50
    return [(norm(x, min_x, max_x), norm(y, min_y, max_y)) for x, y in points]

def normalize_svg_path(svg_d):
    try:
        path = parse_path(svg_d)
        points = get_points_from_path(path)
        if not points: return None
        # --- NEW CHECKS ---
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        
        # Check 1: Bounding Box Size
        # If the original dimensions are near zero, it's a dot/artifact
        if width < 0.1 or height < 0.1:
            return None
            
        # Check 2: Complexity
        # If the path has fewer than 4 distinct points, it's likely just a dot or a single line
        if len(set(points)) < 4:
            return None
        # ------------------
        
        norm_points = normalize_points(points)
        d = f"M {norm_points[0][0]:.2f} {norm_points[0][1]:.2f} " + " ".join(
            f"L {x:.2f} {y:.2f}" for x, y in norm_points[1:]
        ) + " Z"
        return d
    except Exception as e:
        print(f"Error normalizing: {e}")
        return svg_d

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
                
                # Normalize and Validate
                normalized_d = normalize_svg_path(full_d)
                if normalized_d is None:
                    # print(f"⚠️ Skipping {name}: Path is too small or simple.")
                    continue
                data_store[name] = normalized_d
                
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
    
    # Build Vector Index
    build_vector_index(semantic_index)

if __name__ == "__main__":
    run_extraction()
