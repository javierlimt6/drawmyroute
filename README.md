# DrawMyRoute

**AI-Powered Running Route Generator** — Draw shapes on Strava! 🏃‍♂️✨

Built for Hack&Roll 2025.

## Quick Start

### Prerequisites
- **Node.js** 18+
- **Python** 3.10+  
- **Docker Desktop** (for OSRM routing)
- **Mapbox Token** ([get one free](https://account.mapbox.com/))

### 1. Setup OSRM (One-time, ~30 min)

```bash
# Create data directory
mkdir -p ~/osrm-data && cd ~/osrm-data

# Download Singapore/Malaysia map data
curl -L -O https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

# Process data (takes ~25 min)
docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-extract -p /opt/foot.lua /data/malaysia-singapore-brunei-latest.osm.pbf

docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-partition /data/malaysia-singapore-brunei-latest.osrm

docker run -t -v "${PWD}:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-customize /data/malaysia-singapore-brunei-latest.osrm

# Start OSRM server (runs on port 5001)
docker run -d --name osrm -p 5001:5000 -v "${PWD}:/data" \
  ghcr.io/project-osrm/osrm-backend \
  osrm-routed --algorithm mld /data/malaysia-singapore-brunei-latest.osrm
```

Verify: `curl "http://localhost:5001/route/v1/foot/103.8,1.3;103.81,1.31"`

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
echo "MAPBOX_TOKEN=pk.your_token_here" > .env

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: http://localhost:8000

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_token_here" >> .env.local

# Start dev server
npm run dev
```

Frontend runs at: http://localhost:3000

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│    OSRM      │
│  (Next.js)   │     │  (FastAPI)   │     │  (Docker)    │
│  :3000       │     │  :8000       │     │  :5001       │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Available Shapes

| Shape | ID |
|-------|-----|
| ❤️ Heart | `heart` |
| ⭐ Star | `star` |
| 🦖 Dinosaur | `dinosaur` |
| 🟦 Square | `square` |
| 🔺 Triangle | `triangle` |
| 🍌 Banana | `banana` |
| ❄️ Snowflake | `snowflake` |
| 👍 Thumbs Up | `thumbsup` |
| 6️⃣7️⃣ Sixty-Seven | `sixty7` |

## API Reference

### Generate Route
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"shape_id":"heart","start_lat":1.35,"start_lng":103.82,"distance_km":5}'
```

### List Shapes
```bash
curl http://localhost:8000/api/v1/shapes
```

---

## Common Commands

```bash
# Start OSRM (after initial setup)
docker start osrm

# Stop OSRM
docker stop osrm

# Check OSRM status
docker ps | grep osrm

# Restart backend
# (auto-reloads with --reload flag)

# Build frontend for production
cd frontend && npm run build
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OSRM not responding | `docker start osrm` |
| Port 5000 in use | Uses port 5001 instead |
| Frontend can't reach backend | Check `NEXT_PUBLIC_API_URL` in `.env.local` |
| Map not loading | Check `NEXT_PUBLIC_MAPBOX_TOKEN` |

## License

MIT
