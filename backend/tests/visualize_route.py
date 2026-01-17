import httpx
import json
import sys
import random

# Constants
API_URL = "http://localhost:8000/api/v1/generate"
OUTPUT_FILE = "output.geojson"

# Known runnable areas in Singapore
HOTSPOTS = [
    {"name": "Marina Bay", "lat": 1.290270, "lng": 103.851959},
    {"name": "Bishan Park", "lat": 1.362579, "lng": 103.846663},
    {"name": "East Coast Park", "lat": 1.300970, "lng": 103.912239},
    {"name": "Punggol Waterway", "lat": 1.409899, "lng": 103.904323},
    {"name": "Jurong Lake Gardens", "lat": 1.336423, "lng": 103.730761},
    {"name": "Bedok Reservoir", "lat": 1.343110, "lng": 103.924823},
    {"name": "West Coast Park", "lat": 1.296831, "lng": 103.766336}
]

def main():
    # Get shape from command line arg, default to heart
    shape_id = sys.argv[1] if len(sys.argv) > 1 else "heart"
    
    # Pick a random hotspot
    location = random.choice(HOTSPOTS)
    
    print(f"🚀 Generating {shape_id} route at {location['name']}...")
    
    # Add random jitter (approx +/- 500m) to vary the exact start point
    lat_jit = random.uniform(-0.005, 0.005)
    lng_jit = random.uniform(-0.005, 0.005)
    
    payload = {
        "shape_id": shape_id,
        "start_lat": location["lat"] + lat_jit,
        "start_lng": location["lng"] + lng_jit,
        "distance_km": 4.0 # Good distance for these parks
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
        print(f"📏 Distance: {data['distance_m']:.1f} meters")
        print(f"⏱️ Duration: {data['duration_s']/60:.1f} minutes")
        print(f"ℹ️  Shape: {data.get('shape_name', 'Unknown')}")
        
        # Print Strategy & Score details
        print(f"\n📊 Selection Metrics:")
        print(f"🏆 Final Score: {data.get('score', 0):.2f}")
        
        if 'debug_log' in data:
            print("\n📝 Strategy Log:")
            for log in data['debug_log']:
                print(f"   {log}")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Make sure the backend is running: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
