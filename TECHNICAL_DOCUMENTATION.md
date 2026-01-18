# DrawMyRoute - Technical Documentation

> **Hack&Roll 2026** | Team: **duo showdown**

## Executive Summary

DrawMyRoute is an AI-powered fitness application that transforms user prompts, text, or images into GPS-routed running/cycling paths matching any shape. Unlike traditional route planners that optimize for distance or elevation, DrawMyRoute lets users "draw with their feet" by generating complex artistic shapes road-matched to real-world infrastructure.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Core Innovation: The Routing Pipeline](#2-core-innovation-the-routing-pipeline)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Frontend Deep Dive](#4-frontend-deep-dive)
5. [AI & Shape Generation](#5-ai--shape-generation)
6. [Technical Highlights](#6-technical-highlights)
7. [Project Structure](#7-project-structure)

---

## 1. System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Prompt     │  │   Text       │  │   Upload     │  │   Suggest    │    │
│  │  "a heart"   │  │   "NUS"      │  │   🖼️ Image   │  │   ✨ Auto    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js + TypeScript)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Mapbox GL     │  │  Route Resize   │  │   State Mgmt    │              │
│  │   Map Render    │  │    Overlay      │  │    (Hooks)      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI + Python)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         SHAPE ACQUISITION                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │  │
│  │  │   RAG      │  │   Text     │  │  Potrace   │  │   Predefined   │   │  │
│  │  │  Pipeline  │  │  Skeleton  │  │ Vectorize  │  │    Shapes      │   │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │ SVG Path                                │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ROUTE GENERATION ENGINE                           │  │
│  │                                                                        │  │
│  │   1. Point Sampling (svg.path) ──► 2. GPS Projection (geo_scaler)     │  │
│  │                                                                        │  │
│  │   3. Iterative Scaling Loop ──► 4. OSRM Segment Routing               │  │
│  │                                                                        │  │
│  │   5. Unified Scoring ──► 6. Quality Validation                        │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Self-Hosted    │  │   OpenAI        │  │   Nominatim    │              │
│  │  OSRM Server    │  │   GPT-4o/DALL-E │  │   Geocoding    │              │
│  │  (foot profile) │  │                 │  │                 │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14, TypeScript, Ant Design 6 | Responsive SPA with athletic UI |
| **Map** | Mapbox GL JS (Native) | Interactive map visualization |
| **Backend** | FastAPI, Python 3.12 | High-performance async API |
| **AI** | OpenAI GPT-4o, DALL-E, sentence-transformers | Semantic search & generation |
| **Routing** | Self-hosted OSRM (foot.lua profile) | High-concurrency road snapping |
| **Computer Vision** | OpenCV, scikit-image, Potrace | Image vectorization & skeletonization |

---

## 2. Core Innovation: The Routing Pipeline

### The Challenge

Transforming an abstract SVG shape into a real-world runnable route poses several unique challenges:

1. **Coordinate Transformation**: SVG uses 0-100 abstract coordinates; routes need GPS lat/lng
2. **Road Network Constraints**: Not every pixel of a shape maps to a walkable road
3. **Distance Accuracy**: A "5km heart" must actually be ~5km when road-snapped
4. **Shape Fidelity**: The final route should visually resemble the input shape

### The Solution: Iterative Scaling with Unified Scoring

We developed a **4-phase algorithm evolution**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        ALGORITHM EVOLUTION                                  │
├────────────────────────────────────────────────────────────────────────────┤
│  V1: Simple Scaling     │  Fixed size → route → measure → done             │
│      (Mapbox fallback)  │  ⚠️ Often wrong distance, backtracking issues    │
├────────────────────────────────────────────────────────────────────────────┤
│  V2: Multi-Variant      │  Test 16 variants (4 rotations × 4 scales)       │
│      Grid Search        │  ⚠️ Computationally expensive, magical constants │
├────────────────────────────────────────────────────────────────────────────┤
│  V3: Iterative Scaling  │  Adaptive feedback loop with damped convergence  │
│      (Current Default)  │  ✅ Fast, adaptive, unified codebase             │
├────────────────────────────────────────────────────────────────────────────┤
│  V4: Authoritative      │  Direct GPS bounds mapping for resize/move       │
│      Bounds             │  ✅ Instant feedback, no "box snapping" bugs     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Iterative Scaling Algorithm (V3)

```python
# Pseudocode - route_generator.py

def route_with_scaling(points, target_km, start_lat, start_lng):
    scale_factor = 1.0
    
    for iteration in range(MAX_ITERATIONS):  # 4 iterations max
        # 1. Project SVG points to GPS
        gps_points = project_to_gps(points, scale_factor, start_lat, start_lng)
        
        # 2. Route each segment through OSRM
        route = route_segments_parallel(gps_points)
        
        # 3. Measure actual distance
        actual_km = calculate_distance(route)
        
        # 4. Check convergence (±30% tolerance)
        if 0.7 <= actual_km / target_km <= 1.3:
            return route  # Success!
        
        # 5. Adaptive adjustment with damping
        adjustment = target_km / actual_km
        scale_factor *= (1.0 + (adjustment - 1.0) * DAMPING)  # 0.6 damping

    return route  # Best effort after 4 iterations
```

### Unified Scoring System

Every route candidate is evaluated on a **0-100 scale**:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Distance Accuracy** | 40% | `1.0 - abs(actual_km - target_km) / target_km` |
| **Road Coverage** | 40% | Ratio of successfully routed segments (penalizes "jumps") |
| **Loop Closure** | 20% | Proximity of start/end points (`1.0 / (gap_m / 100 + 1)`) |

**Quality Gate**: Routes scoring <40 or with >25% failed segments are rejected.

---

## 3. Backend Deep Dive

### Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints
│   ├── data/
│   │   ├── shapes.json        # Curated predefined shapes
│   │   ├── paths.json         # 500+ Lucide icons (merged store)
│   │   ├── data_store.json    # Core shape library
│   │   ├── material_store.json # Google Material Icons
│   │   ├── prompt_cache.json  # LLM result cache
│   │   └── vector_index.pkl   # Sentence embeddings
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   └── services/
│       ├── shape_service.py      # Main orchestrator
│       ├── route_generator.py    # Iterative scaling engine
│       ├── scoring.py            # Unified scoring system
│       ├── routing_config.py     # Centralized constants
│       ├── geo_scaler.py         # SVG→GPS projection
│       ├── osrm_router.py        # OSRM segment routing
│       ├── llm_service.py        # RAG pipeline + DALL-E
│       ├── text_to_svg.py        # Text skeletonization
│       ├── image_to_svg.py       # Potrace vectorization
│       ├── suggest_service.py    # Auto-suggest engine
│       ├── svg_parser.py         # SVG point sampling
│       ├── gpx_exporter.py       # Strava/Garmin export
│       └── map_matcher.py        # Mapbox fallback
└── requirements.txt
```

### Core Services Explained

#### `shape_service.py` - The Orchestrator

**Purpose**: Entry point for all route generation. Coordinates between input modes (prompt/text/image/shape) and the route generator.

```python
# Key Functions
get_svg_path_and_metadata(shape_id, prompt, text, image_svg_path)
    → Returns (svg_path, shape_name, shape_id)

generate_route(shape_id, start_lat, start_lng, distance_km, ...)
    → Standard generation with iterative scaling

generate_route_with_bounds(shape_id, min_lat, max_lat, min_lng, max_lng, ...)
    → Authoritative bounds generation for resize/move operations
```

#### `osrm_router.py` - Self-Hosted Routing Engine

**Purpose**: High-concurrency segment routing using our custom OSRM instance.

**Key Innovation**: We deploy OSRM with a custom `foot.lua` profile that:
- Routes through pedestrian paths, void decks, and park connectors
- Ignores car-only restrictions
- Enables 100+ concurrent routing requests/second

```python
# Flexible Waypoint Routing
async def route_segment(start, end):
    # If detour > 10x straight-line distance, skip the waypoint
    if actual_distance / straight_line > DETOUR_THRESHOLD:
        return fallback_to_skip(start, end)
```

#### `geo_scaler.py` - Coordinate Projection

**Purpose**: Transforms 0-100 SVG coordinates to real-world GPS coordinates.

**Key Math**:
```python
# Perimeter-Based Scaling with Road Detour Factor
abstract_perimeter = calculate_perimeter(svg_points)
scale_km = (distance_km / ROAD_DETOUR_FACTOR) / abstract_perimeter  # 1.4x factor

# Y-Axis Inversion (SVG Y↓ but GPS Lat↑)
lat = start_lat - (normalized_y * scale_km / 111.32)
lng = start_lng + (normalized_x * scale_km / (111.32 * cos(start_lat)))
```

---

## 4. Frontend Deep Dive

### Directory Structure

```
frontend/src/
├── app/
│   ├── layout.tsx           # Root layout with Ant Design
│   ├── page.tsx             # Main application (1376 lines)
│   └── globals.css          # Strava-themed styles
├── components/
│   ├── Map.tsx              # Mapbox GL wrapper
│   └── RouteResizeOverlay.tsx  # Interactive drag handles
├── hooks/
│   └── use-location.tsx     # Geolocation hook
└── lib/
    ├── api.ts               # Type-safe API client
    └── geocoding.ts         # Nominatim address search
```

### Key UI Components

#### Main Page (`page.tsx`)

The heart of the application - a **1376-line** component managing:

- **4 Input Modes**: Prompt, Text, Upload, Suggest
- **Distance Control**: 0-50km slider with km/mi toggle
- **Location Search**: Debounced autocomplete via Nominatim
- **Route Visualization**: Dual-layer GeoJSON rendering
- **Results Panel**: Slide-up stats with GPX export

```typescript
// Key State Management
const [mode, setMode] = useState<InputMode>("type");  // type|text|image|draw
const [distance, setDistance] = useState(25);          // km
const [route, setRoute] = useState<GeoJSON | null>(null);
const [svgPath, setSvgPath] = useState<string>("");   // Current shape path
const [isGenerating, setIsGenerating] = useState(false);
```

#### Route Resize Overlay (`RouteResizeOverlay.tsx`)

An **interactive bounding box overlay** providing Canva-style drag handles:

- **Edge Handles**: 8 resize handles at corners and edges
- **Center Drag**: Invisible interior area for route repositioning
- **SVG Preview**: Semi-transparent blue shape overlay (0.2 opacity)
- **Authoritative Bounds**: Final GPS coordinates sent to backend

```typescript
// Authoritative Bounds Pattern
const handleResizeEnd = (bounds: Bounds) => {
    // Send exact GPS coordinates - no recalculation on backend
    api.generateRouteWithBounds({
        target_bounds: {
            min_lat: bounds.minLat,
            max_lat: bounds.maxLat,
            min_lng: bounds.minLng,
            max_lng: bounds.maxLng
        }
    });
};
```

### Strava-Inspired Design System

| Element | Implementation |
|---------|----------------|
| **Primary Color** | `#FC4C02` (Strava Orange) |
| **Dark Mode** | `#1A1A1A` background |
| **Route Line** | Dual-layer: 8px white outline + 5px orange |
| **Typography** | Athletic bold headers |
| **Motion** | CSS `@keyframes slideUp` for bottom sheet |

---

## 5. AI & Shape Generation

### Multi-Modal Shape Acquisition

DrawMyRoute supports **4 input modes**, each with a dedicated generation pipeline:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        SHAPE ACQUISITION MODES                              │
├─────────────────┬──────────────────────────────────────────────────────────┤
│  MODE           │  PIPELINE                                                 │
├─────────────────┼──────────────────────────────────────────────────────────┤
│  Quick Pick     │  shapes.json → Direct SVG lookup                         │
│  (Predefined)   │                                                          │
├─────────────────┼──────────────────────────────────────────────────────────┤
│  Prompt         │  RAG Pipeline:                                           │
│  "a happy dog"  │  1. Cache lookup                                         │
│                 │  2. Vector search (500+ icons)                           │
│                 │  3. LLM re-ranking (GPT-4o-mini)                         │
│                 │  4. DALL-E fallback → Potrace vectorization             │
├─────────────────┼──────────────────────────────────────────────────────────┤
│  Text           │  Multi-Stroke Skeletonization:                           │
│  "NUS"          │  1. PIL text rendering                                   │
│                 │  2. scikit-image skeletonize()                           │
│                 │  3. OpenCV contour detection                             │
│                 │  4. RDP simplification → SVG path                        │
├─────────────────┼──────────────────────────────────────────────────────────┤
│  Upload         │  Potrace Vectorization:                                  │
│  🖼️ Image       │  1. Image preprocessing (grayscale, threshold)           │
│                 │  2. potracer bitmap tracing                              │
│                 │  3. Bezier → Point sampling → SVG path                   │
├─────────────────┼──────────────────────────────────────────────────────────┤
│  Auto-Suggest   │  Parallel Evaluation:                                    │
│  ✨ One-Click   │  1. Sample 10 random shapes from library                 │
│                 │  2. Generate routes in parallel                          │
│                 │  3. Return highest-scoring valid route                   │
└─────────────────┴──────────────────────────────────────────────────────────┘
```

### RAG Pipeline Details (llm_service.py)

Our **5-stage Retrieval-Augmented Generation** pipeline:

```python
# Stage 1: Cache Hit (instant)
if prompt.lower() in prompt_cache:
    return prompt_cache[prompt.lower()]

# Stage 2: Vector Search (semantic similarity)
query_embedding = model.encode(prompt)
candidates = cosine_similarity(query_embedding, icon_embeddings)[:15]

# Stage 3: LLM Re-Ranking (GPT-4o-mini)
response = openai.chat.completions.create(
    messages=[{
        "role": "system",
        "content": "You MUST select the best matching icon. Pick creatively!"
    }]
)

# Stage 4: Vector Safety Net (if LLM returns NONE)
if response == "NONE":
    return candidates[0]  # Top vector match

# Stage 5: DALL-E Fallback (expensive, last resort)
image = dalle.generate("black silhouette on white: " + prompt)
svg_path = potrace_vectorize(image)
```

### Text Skeletonization Pipeline (text_to_svg.py)

Converts literal text like "NUS" or "67" into single-line runnable paths:

```
"NUS" → ┌─────────────────────────────────────────────────────────┐
        │  1. Render text to high-res bitmap (PIL ImageFont)      │
        │                                                          │
        │  2. Skeletonize to centerlines (scikit-image)           │
        │     █████    ─────                                       │
        │     █   █ →  │   │  (single-pixel paths)                │
        │     █████    ─────                                       │
        │                                                          │
        │  3. Detect contours (OpenCV)                            │
        │                                                          │
        │  4. Simplify with RDP algorithm                         │
        │                                                          │
        │  5. Assemble multi-stroke SVG path                      │
        │     "M 10,50 L 10,0 L 10,50 L 30,0 M 40,50 L 40,0..."   │
        └─────────────────────────────────────────────────────────┘
```

**Why Skeletonization over Outlines?**
- Outlines create a route that traces *around* letters (confusing for runners)
- Skeletons create a route that traces *through* letters (natural running path)

---

## 6. Technical Highlights

### 🚀 Self-Hosted OSRM Server

**Problem**: Commercial routing APIs (Google, Mapbox) are:
- Expensive at scale
- Rate-limited
- Don't support pedestrian-specific paths

**Solution**: We deployed OpenStreetMap Routing Machine (OSRM) with a custom `foot.lua` profile:

```lua
-- Custom foot profile enables:
-- ✅ Pedestrian paths and sidewalks
-- ✅ HDB void decks (Singapore-specific)
-- ✅ Park connectors and cycling paths
-- ✅ 100+ concurrent requests/second
-- ❌ Highways and car-only roads
```

### 🎯 Perimeter-Based Scaling

**Problem**: When asking for a "5km heart", how big should the abstract shape be?

**Solution**: We calculate the abstract perimeter and apply a **Road Detour Factor** (1.4x):

```
Target Distance: 5km
Road Detour Factor: 1.4x (roads are ~40% longer than straight lines)
Effective Perimeter: 5km / 1.4 = 3.57km abstract

If heart perimeter in 0-100 space = 400 units
Scale factor = 3.57km / 400 = 0.00893km/unit
```

### 🔁 Flexible Waypoint Routing

**Problem**: Some shape points land in water, military zones, or other unroutable areas.

**Solution**: Detect and skip outlier waypoints:

```python
# osrm_router.py
DETOUR_THRESHOLD = 10.0

for i, segment in enumerate(segments):
    straight_line = haversine(segment.start, segment.end)
    routed_distance = osrm.route(segment.start, segment.end)
    
    if routed_distance / straight_line > DETOUR_THRESHOLD:
        # Skip this waypoint - it's probably in water!
        skip_indices.append(i)
```

### 📦 Arc-Aware SVG Scaling

**Problem**: Standard icon libraries (Lucide, Material) use 24x24 viewBox, but our system expects 0-100.

**Challenge**: SVG arc commands have **binary flags** (0 or 1) that must NOT be scaled:

```
A 10 10 0 0 1 20 30
    ↑  ↑ ↑ ↑ ↑  ↑  ↑
    rx ry rot large-arc sweep-flag x y
              ↑        ↑
              BINARY (0/1) - DO NOT SCALE!
```

**Solution**: Character-by-character parser that preserves binary flags:

```python
# llm_service.py → _scale_24_to_100()
def _scale_24_to_100(svg_path: str) -> str:
    SCALE = 4.167  # 100/24
    # Parse each command, scale coordinates, preserve arc flags
    ...
```

### ⚡ Sub-500ms Fast Mode

**Problem**: Interactive resize/move needs instant feedback, but full generation takes 2-3 seconds.

**Solution**: Tiered point density:

| Mode | Points | Use Case |
|------|--------|----------|
| **Fast Mode** | 50 | Interactive drag operations |
| **Standard** | 80 | Final generation |
| **Suggest** | 150 | Auto-suggest candidates |

---

## 7. Project Structure

### Complete File Tree

```
drawmyroute/
├── backend/
│   ├── app/
│   │   ├── api/routes.py           # 6 endpoints
│   │   ├── config.py               # Environment settings
│   │   ├── main.py                 # FastAPI app
│   │   ├── models/schemas.py       # Pydantic models
│   │   ├── data/
│   │   │   ├── shapes.json         # 15 curated shapes
│   │   │   ├── paths.json          # 500+ merged icons
│   │   │   ├── data_store.json     # Lucide icons
│   │   │   ├── material_store.json # Material icons
│   │   │   ├── vector_index.pkl    # Embeddings cache
│   │   │   └── prompt_cache.json   # LLM result cache
│   │   ├── services/
│   │   │   ├── shape_service.py    # ~290 lines - orchestrator
│   │   │   ├── route_generator.py  # ~250 lines - core algorithm
│   │   │   ├── scoring.py          # ~130 lines - unified scoring
│   │   │   ├── routing_config.py   # ~50 lines - constants
│   │   │   ├── geo_scaler.py       # ~200 lines - GPS projection
│   │   │   ├── osrm_router.py      # ~280 lines - OSRM integration
│   │   │   ├── llm_service.py      # ~270 lines - RAG pipeline
│   │   │   ├── text_to_svg.py      # ~170 lines - skeletonization
│   │   │   ├── image_to_svg.py     # ~350 lines - Potrace
│   │   │   ├── suggest_service.py  # ~170 lines - auto-suggest
│   │   │   ├── svg_parser.py       # ~50 lines - point sampling
│   │   │   ├── gpx_exporter.py     # ~80 lines - Strava export
│   │   │   └── map_matcher.py      # ~100 lines - Mapbox fallback
│   │   └── utils/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # ~1376 lines - main UI
│   │   │   ├── layout.tsx          # Root layout
│   │   │   └── globals.css         # Strava theme
│   │   ├── components/
│   │   │   ├── Map.tsx             # Mapbox wrapper
│   │   │   └── RouteResizeOverlay.tsx  # Drag handles
│   │   ├── hooks/use-location.tsx  # Geolocation
│   │   └── lib/
│   │       ├── api.ts              # Type-safe API client
│   │       └── geocoding.ts        # Address search
│   ├── package.json
│   └── tsconfig.json
│
├── TECHNICAL_DOCUMENTATION.md      # This file
├── README.md                       # Quick start guide
├── DEVPOST.md                      # Submission writeup
└── architecture.md                 # High-level diagrams
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/generate` | POST | Generate route from any input mode |
| `/api/v1/parse-image` | POST | Upload image → extract SVG path |
| `/api/v1/suggest` | POST | Auto-suggest best matching route |
| `/api/v1/shapes` | GET | List all predefined shapes |
| `/api/v1/export/gpx` | POST | Export route as GPX file |
| `/health` | GET | Health check |

### Key Algorithms Summary

| Algorithm | Location | Purpose |
|-----------|----------|---------|
| Iterative Scaling | `route_generator.py` | Adaptive distance fitting |
| Unified Scoring | `scoring.py` | Route quality evaluation |
| Flexible Waypoint Routing | `osrm_router.py` | Skip unroutable points |
| Perimeter-Based Scaling | `geo_scaler.py` | SVG→GPS projection |
| RAG Pipeline | `llm_service.py` | Semantic shape search |
| Multi-Stroke Skeletonization | `text_to_svg.py` | Text→SVG conversion |
| Potrace Vectorization | `image_to_svg.py` | Image→SVG tracing |

---

## Running the Application

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### OSRM Server (Separate Container)

```bash
# Pull Singapore OSM data
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/singapore.osm.pbf
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-partition /data/singapore.osrm
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-customize /data/singapore.osrm

# Start server
docker run -t -p 5001:5000 -v $(pwd):/data osrm/osrm-backend osrm-routed /data/singapore.osrm
```

---

## Conclusion

DrawMyRoute represents a novel intersection of:
- **AI-powered shape generation** (RAG, DALL-E, skeletonization)
- **Real-time geographic computation** (self-hosted routing engine)
- **Modern web development** (responsive, athletic-themed interface)
- **Elegant algorithm design** (iterative scaling, unified scoring)

The project transforms the simple idea of "running in a shape" into a sophisticated pipeline that handles everything from semantic prompts to GPS coordinates, making fitness more creative and engaging.

---

*Built for Hack&Roll 2026 by team duo showdown* 🏃‍♂️
