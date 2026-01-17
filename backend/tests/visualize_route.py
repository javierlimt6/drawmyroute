import httpx
import json
import sys
import random

# Constants
API_URL = "http://localhost:8000/api/v1/generate"
OUTPUT_FILE = "output.geojson"

def main():
    # Get shape from command line arg, default to heart
    shape_id = sys.argv[1] if len(sys.argv) > 1 else "heart"
    
    print(f"🚀 Generating route for shape: {shape_id}...")
    
    # Singapore CBD / Marina Bay
    # Add tiny random jitter to ensure unique request
    lat_jit = random.uniform(-0.001, 0.001)
    lng_jit = random.uniform(-0.001, 0.001)
    
    payload = {
        "shape_id": shape_id,
        "start_lat": 1.290270 + lat_jit,
        "start_lng": 103.851959 + lng_jit,
        "distance_km": 3.0
    }
    
    print(f"📍 Start Location: {payload['start_lat']:.6f}, {payload['start_lng']:.6f}")
    
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
        print(f"ℹ️  Shape: {data.get('shape_name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Make sure the backend is running: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
