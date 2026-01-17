import sys
import os
from pathlib import Path

# Add backend directory to path so we can import app
BACKEND_DIR = Path(__file__).parent.parent
sys.path.append(str(BACKEND_DIR))

from app.services.llm_service import _get_best_icon_match

# Test Cases: (Prompt, List of Acceptable Answers)
# Note: "acceptable" lists are not exhaustive, just likely candidates from Lucide
TEST_CASES = [
    # Emotions / Concepts
    ("Love", ["heart", "heart-handshake", "hand-heart", "heart-pulse"]),
    ("I like this", ["thumbs-up", "heart", "star", "smile"]),
    ("Warning danger", ["triangle-alert", "shield-alert", "skull", "alert-circle", "octagon-alert"]),
    ("Great idea", ["lightbulb", "sparkles", "zap"]),
    ("Time to go", ["clock", "watch", "timer", "hourglass"]),
    
    # Nature / Animals
    ("A running dog", ["dog", "paw-print", "bone", "rabbit"]),
    ("Cat", ["cat", "paw-print"]),
    ("Tree", ["tree-pine", "tree-deciduous", "trees", "palm-tree", "leaf"]),
    ("Flower", ["flower", "flower-2", "tulip", "rose", "clover"]),
    ("Sunny day", ["sun", "sun-medium", "cloud-sun"]),
    
    # Technology
    ("Wifi signal", ["wifi", "signal", "rss"]),
    ("Database storage", ["database", "hard-drive", "server"]),
    ("Secure password", ["lock", "key", "shield-check"]),
    ("Coding script", ["code", "file-code", "terminal", "braces"]),
    ("Take a photo", ["camera", "aperture", "image"]),
    
    # Everyday Objects
    ("Coffee break", ["coffee", "cup-soda", "mug"]),
    ("Reading a book", ["book", "book-open", "library"]),
    ("Shopping", ["shopping-cart", "shopping-bag", "store"]),
    ("Listen to music", ["music", "headphones", "speaker", "volume-2"]),
    ("House", ["house", "home"]),
    
    # UI Actions
    ("Settings", ["settings", "cog", "sliders", "gear"]),
    ("Delete item", ["trash", "trash-2", "x", "delete", "bucket"]),
    ("Edit text", ["pencil", "pen", "edit", "file-pen"]),
    ("Search for file", ["search", "file-search", "zoom-in"]),
    ("Download", ["download", "arrow-down", "save", "import"]),
    
    # Abstract
    ("Success", ["check", "circle-check", "award", "trophy", "thumbs-up"]),
    ("Fail", ["x", "circle-x", "ban", "thumbs-down"]),
    ("Question", ["help-circle", "circle-question", "question-mark", "circle-help"]),
    ("Navigation", ["map", "compass", "navigation", "route"]),
    ("Money", ["dollar-sign", "coins", "banknote", "wallet", "credit-card"]),
]

def run_tests():
    print(f"🚀 Running {len(TEST_CASES)} semantic matching tests...")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for prompt, acceptable in TEST_CASES:
        try:
            print(f"Query: '{prompt}'", end=" ... ")
            result = _get_best_icon_match(prompt)
            
            if not result:
                print(f"❌ FAIL -> No match found")
                failed += 1
                continue

            # Check if result matches any of the acceptable answers (exact or contains)
            # Or if the result is semantically very close (hard to judge automatically)
            
            if result in acceptable:
                print(f"✅ PASS -> '{result}'")
                passed += 1
            else:
                # Also accept if the result contains the main keyword of expected
                is_partial = False
                for acc in acceptable:
                    if acc in str(result) or str(result) in acc:
                        is_partial = True
                        break
                
                if is_partial:
                    print(f"⚠️  CLOSE -> '{result}' (Expected: {acceptable})")
                    passed += 1 
                else:
                    print(f"❌ FAIL -> '{result}' (Expected: {acceptable})")
                    failed += 1
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
            
    print("-" * 60)
    print(f"Results: {passed} Passed, {failed} Failed")
    accuracy = (passed / len(TEST_CASES)) * 100
    print(f"Accuracy: {accuracy:.1f}%")

if __name__ == "__main__":
    run_tests()
