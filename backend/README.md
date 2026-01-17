# DrawMyRoute Backend

FastAPI backend for generating running/cycling routes from predefined shapes using Mapbox Map Matching.

## Tech Stack

- **Framework:** FastAPI
- **SVG Parsing:** svg.path
- **Map Matching:** Mapbox Map Matching API
- **HTTP Client:** httpx
- **Language:** Python 3.10+

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- Mapbox account (for Map Matching API token)

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
MAPBOX_TOKEN=pk.your_mapbox_token_here
```

Get your token from [Mapbox Account](https://account.mapbox.com/access-tokens/).

### Run Development Server

```bash
uvicorn app.main:app --reload
```

API available at [http://localhost:8000](http://localhost:8000)

Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

### `GET /api/v1/shapes`

List all available predefined shapes.

**Response:**
```json
{
  "heart": { "name": "Heart", "svg_path": "M 50 25 C...", "thumbnail": "/assets/heart.png" },
  "star": { "name": "Star", "svg_path": "M 50 0 L...", "thumbnail": "/assets/star.png" },
  "dinosaur": { "name": "Dinosaur", "svg_path": "M 10 70 L...", "thumbnail": "/assets/dino.png" }
}
```

### `POST /api/v1/generate`

Generate a route from a predefined shape.

**Request:**
```json
{
  "shape_id": "heart",
  "start_lat": 1.3521,
  "start_lng": 103.8198,
  "distance_km": 5.0
}
```

**Response:**
```json
{
  "shape_id": "heart",
  "shape_name": "Heart",
  "route": {
    "type": "LineString",
    "coordinates": [[103.82, 1.35], [103.83, 1.36], ...]
  },
  "distance_m": 5123,
  "duration_s": 3074,
  "original_points": [[50, 25], [0, 50], ...],
  "gps_points": [[1.35, 103.82], [1.36, 103.83], ...]
}
```

### `GET /health`

Health check endpoint.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py        # API endpoint definitions
│   ├── data/
│   │   └── shapes.json      # Predefined SVG shapes
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── services/
│   │   ├── geo_scaler.py    # Abstract → GPS coordinate conversion
│   │   ├── map_matcher.py   # Mapbox Map Matching API client
│   │   ├── shape_service.py # Main orchestration service
│   │   └── svg_parser.py    # SVG path sampling
│   ├── config.py            # Settings from environment
│   └── main.py              # FastAPI app entry point
├── tests/
├── requirements.txt
└── .env                     # Environment variables (create this)
```

## How It Works

1. **Receive request** with shape_id, start location, and target distance
2. **Load SVG path** from `shapes.json`
3. **Sample points** from SVG path using `svg.path`
4. **Scale to GPS** coordinates based on start location and distance
5. **Snap to roads** using Mapbox Map Matching API
6. **Return GeoJSON** LineString for frontend to render

## Adding New Shapes

Edit `app/data/shapes.json`:

```json
{
  "new_shape": {
    "name": "New Shape",
    "svg_path": "M 0 0 L 100 0 L 100 100 L 0 100 Z",
    "thumbnail": "/assets/new_shape.png"
  }
}
```

SVG paths should use a 0-100 coordinate system.

## Testing

```bash
# Test shape list
curl http://localhost:8000/api/v1/shapes

# Test generation
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"shape_id":"heart","start_lat":1.3521,"start_lng":103.8198,"distance_km":5}'
```

## Deployment

Deploy to Railway, Render, or Fly.io:

1. Set `MAPBOX_TOKEN` environment variable
2. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## License

MIT
