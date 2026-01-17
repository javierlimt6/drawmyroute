import httpx
import json
import sys

# Constants
API_URL = "http://localhost:8000/api/v1/generate"
OUTPUT_FILE = "output.geojson"

def main():
    print("🚀 Generating route...")
    
    # Singapore Coordinates (around Marina Bay)
    payload = {
        "shape_id": "heart",
        "start_lat": 1.3521,
        "start_lng": 103.8198,
        "distance_km": 5.0
    }
    
    try:
        response = httpx.post(API_URL, json=payload, timeout=30.0)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            sys.exit(1)
            
        data = response.json()
        route_geojson = data["route"]
        
        # Save to file
        with open(OUTPUT_FILE, "w") as f:
            json.dump(route_geojson, f, indent=2)
            
        print(f"✅ Route generated successfully!")
        print(f"📍 Saved to: {OUTPUT_FILE}")
        print(f"📏 Distance: {data['distance_m']} meters")
        print(f"⏱️ Duration: {data['duration_s']} seconds")
        print(f"\n💡 Tip: Drag {OUTPUT_FILE} into https://geojson.io to visualize it.")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Make sure the backend is running: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
