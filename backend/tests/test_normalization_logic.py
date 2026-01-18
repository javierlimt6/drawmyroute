
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

    # Case 1: Square (2,2) to (22,22)
    # 24x24 bounds. Min=2, Max=22.
    # Width=20, Height=20. Aspect Ratio 1:1.
    # Should scale to 0-100 on both axes.
    input_path = "M 2 2 L 22 2 L 22 22 L 2 22 Z"
    
    print(f"\nTest 1: Square '{input_path}'")
    result = normalize_svg_path(input_path)
    print(f"Result: {result}")
    
    # We expect floats with 2 decimal places
    if result and "M 0.00 0.00" in result and "100.00 100.00" in result:
        print("✅ Test 1 Passed")
    else:
        print("❌ Test 1 Failed")

    # Case 2: Rectangle (2,2) to (22,12)
    # Width = 20, Height = 10. Aspect Ratio = 2:1.
    # New Logic: Scale by max dim (20). Scale factor = 100/20 = 5.
    # X range: 0 to 100.
    # Y range: Should be centered. Height 10 * 5 = 50.
    # So Y should be from 25 to 75.
    input_path_2 = "M 2 2 L 22 2 L 22 12 L 2 12 Z"
    print(f"\nTest 2: Rectangle '{input_path_2}'")
    result_2 = normalize_svg_path(input_path_2)
    print(f"Result: {result_2}")
    
    # Check X limits
    if "0.00" in result_2 and "100.00" in result_2:
        print("✅ X-Axis Scaled to 0-100")
    else:
        print("❌ X-Axis Scaling Failed")

    # Check Y limits (should be around 25.00 and 75.00)
    if "25.00" in result_2 and "75.00" in result_2:
        print("✅ Y-Axis Preserved Aspect Ratio (25-75)")
    else:
        print("❌ Y-Axis Aspect Ratio Failed (Expected 25.00 and 75.00)")

if __name__ == "__main__":
    test_normalization()
