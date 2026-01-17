
import sys
import os
from pathlib import Path

# Setup paths
# current file: backend/tests/test_normalization_logic.py
current_dir = Path(__file__).parent
backend_dir = current_dir.parent          # backend/
scripts_dir = backend_dir / "scripts"     # backend/scripts/

# Add both to sys.path
# scripts_dir needed to find 'prepare_assets'
sys.path.append(str(scripts_dir))
# backend_dir needed because prepare_assets imports 'app'
sys.path.append(str(backend_dir))

try:
    from prepare_assets import normalize_svg_path
except ImportError as e:
    print(f"Failed to import prepare_assets: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

def test_normalization():
    print("🧪 Testing SVG Normalization Logic...")

    # Case 1: Simple Diagonal Line (2,2) to (22,22)
    # 24x24 bounds. Min=2, Max=22.
    # Normalization:
    # x: 2 -> 0, 22 -> 100
    # y: 2 -> 0, 22 -> 100
    input_path = "M 2 2 L 22 22"
    
    print(f"\nTest 1: Diagonal Line '{input_path}'")
    result = normalize_svg_path(input_path)
    print(f"Result: {result}")
    
    # We expect floats with 2 decimal places
    if "M 0.00 0.00" in result and "L 100.00 100.00" in result:
        print("✅ Test 1 Passed")
    else:
        print("❌ Test 1 Failed")

    # Case 2: Rectangle (2,2) to (22,12)
    # x range: 2 to 22 (width 20) -> maps to 0-100
    # y range: 2 to 12 (height 10) -> maps to 0-100 (independent normalization)
    input_path_2 = "M 2 2 L 22 2 L 22 12 L 2 12 Z"
    print(f"\nTest 2: Rectangle '{input_path_2}'")
    result_2 = normalize_svg_path(input_path_2)
    print(f"Result: {result_2}")
    
    if "0.00" in result_2 and "100.00" in result_2:
        print("✅ Test 2 Passed (Scaled to 0-100 range independently)")
    else:
        print("❌ Test 2 Failed")

if __name__ == "__main__":
    test_normalization()
