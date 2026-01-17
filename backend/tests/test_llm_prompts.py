import sys
import os
from pathlib import Path

# Add backend directory to path so we can import app
BACKEND_DIR = Path(__file__).parent.parent
sys.path.append(str(BACKEND_DIR))

from app.services.llm_service import _get_best_icon_match

# Test Cases: (Prompt, List of Acceptable Answers)
# Note: "acceptable" lists are not exhaustive, just likely candidates from Lucide
# Test Cases: (Prompt, List of Acceptable Answers from your provided icon set)
TEST_CASES = [
    # Emotions / Concepts (Using your heart and warning icons)
    ("Love", ["heart", "hand-heart", "heart-crack", "message-circle-heart", "message-square-heart", "heart-pulse"]),
    ("I like this", ["thumbs-up", "smile", "laugh", "heart", "star", "message-circle-heart"]),
    ("Warning danger", ["triangle-alert", "shield-alert", "octagon-alert", "skull", "siren", "message-square-warning"]),
    ("Great idea", ["lightbulb", "sparkle", "sparkles", "zap", "zap-off"]),
    ("Time to go", ["clock", "watch", "alarm-clock", "hourglass", "timer-off"]),
    
    # Nature / Animals (Panda and Dog are explicitly in your list)
    ("A running dog", ["dog", "paw-print", "bone", "footprints"]),
    ("Cat", ["cat", "paw-print"]),
    ("Panda bear", ["panda", "paw-print"]),
    ("Tree", ["trees", "tree-pine", "tree-deciduous", "shrub", "leaf"]),
    ("Flower", ["flower", "flower-2", "rose"]),
    ("Sunny day", ["sun", "sun-medium", "cloud-sun", "sunrise", "sunset"]),
    
    # Technology (Focusing on network and storage tags)
    ("Wifi signal", ["wifi", "wifi-high", "wifi-low", "signal", "signal-high", "antenna"]),
    ("Database storage", ["database", "hard-drive", "server-off", "monitor-cloud", "archive", "warehouse"]),
    ("Secure password", ["lock", "key-round", "shield-check", "vault", "fingerprint-pattern"]),
    ("Coding script", ["code", "file-code", "terminal", "braces", "regex", "cpu", "brain-circuit"]),
    ("Take a photo", ["camera", "aperture", "image", "instagram"]),
    
    # Everyday Objects
    ("Coffee break", ["coffee", "cup-soda", "glass-water", "mug"]),
    ("Reading a book", ["book-open", "book-text", "library-big", "book-open-text", "notebook"]),
    ("Shopping", ["shopping-cart", "shopping-bag", "store", "shopping-basket", "baggage-claim"]),
    ("Listen to music", ["music", "headphones", "headset", "speaker", "volume-2", "disc-album"]),
    ("House", ["house", "house-wifi", "house-heart", "building-2"]),
    
    # UI Actions
    ("Settings", ["settings", "cog", "sliders-horizontal", "wrench", "bolt"]),
    ("Delete item", ["trash", "trash-2", "x", "octagon-x", "file-minus", "delete"]),
    ("Edit text", ["pencil", "pen", "square-pen", "file-pen", "pencil-line", "brush"]),
    ("Search for file", ["search", "file-search", "scan-search", "binoculars", "telescope"]),
    ("Download", ["download", "file-down", "hard-drive-download", "arrow-big-down", "import"]),
    
    # Abstract
    ("Success", ["check", "circle-check", "award", "trophy", "medal", "party-popper", "badge-check"]),
    ("Fail", ["circle-x", "octagon-x", "thumbs-down", "shield-x", "ban", "bomb"]),
    ("Question", ["badge-question-mark", "circle-question-mark", "mail-question-mark", "help-circle"]),
    ("Navigation", ["map", "compass", "map-pin", "map-pinned", "milestone", "route"]),
    ("Money", ["dollar-sign", "coins", "banknote", "piggy-bank", "wallet", "badge-dollar-sign", "receipt-cent"]),
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
