# DrawMyRoute - DevPost Submission

> **Turn any shape into a runnable route — powered by AI and real-time road mapping.**

---

## Inspiration

We wanted to transform the mundane daily run into a creative act. What if you could literally *draw* your workout? Whether it's tracing your university logo, spelling out a name, or running a custom shape, DrawMyRoute makes GPS art accessible to everyone.

---

## What It Does

DrawMyRoute takes any visual input — a text prompt, a hand-drawn sketch, typed text, or an uploaded image — and transforms it into a real, runnable route on actual roads and paths.

**Key Features:**
- 🎨 **4 Input Modes:** Prompt (describe a shape), Draw (freehand sketch), Text (type letters/numbers), Upload (images/SVGs)
- 🗺️ **Interactive Map:** Drag, resize, and reposition your shape anywhere in Singapore
- 📏 **Smart Scaling:** Routes automatically adapt to your target distance
- 📤 **GPX Export:** One-click export to Strava, Garmin, and other fitness apps

---

## How We Built It

### Frontend
- **Next.js + React** with a Strava-inspired dark theme
- **Leaflet.js** for interactive map rendering with custom overlays
- Real-time SVG preview that updates as you modify bounds

### Backend
- **FastAPI** (Python) serving the core routing logic
- **Self-hosted OSRM** (OpenStreetMap Routing Machine) for sub-50ms segment routing
- **Gemini 2.0 Flash** for prompt-to-shape generation (RAG-enhanced with 500+ icon library)
- **Potrace** for image-to-SVG vectorization
- **FreeType** for text-to-centerline path generation

---

## Technical Achievements

### 1. Multi-Variant Parallel Optimization
Instead of a single guess, our routing engine tests **16 route candidates simultaneously** (4 rotations × 4 scales) for every request.
- **Scoring Algorithm:** Weighted model — 65% Fidelity, 25% Distance Accuracy, 10% Loop Closure
- **Performance:** Python `asyncio` + `httpx` delivers final selection in <2 seconds

### 2. Perimeter-Preserving Interactive Resize
Custom geometric scaling keeps route distance stable during interactive resizing.
- **The Math:** Inverse geometric relationship (`√aspect_ratio`) — stretching vertically auto-contracts horizontally
- **Benefit:** Prevents "distance explosion" when changing aspect ratios

### 3. Sub-500ms "Fast Mode" Interaction
Maintains 60fps UI during dragging/resizing with a streamlined generator.
- **Optimization:** Drops point density (80 → 40 pts) and disables multi-rotation search for instant visual feedback

### 4. Advanced Path Extraction Pipelines
- **Image-to-SVG (Potrace):** Binary thresholding + vectorization turns raster uploads into clean centerlines
- **Text-to-SVG (Skeletonization):** Centerline extraction ensures runners follow letter *strokes*, not perimeters
- **500+ Shape Library:** Lucide-based icons, normalized and arc-aware (preserving binary flags for SVG parsing)

### 5. Self-Hosted OSRM Infrastructure
Deployed our own OSRM server to bypass rate limits and latency.
- **Capacity:** 100+ requests/second for Singapore's entire road network
- **Customization:** Custom `foot.lua` profile tuned for urban runners (void decks, park connectors)

---

## Challenges We Ran Into

### The "Zig-Zag" Problem
**Challenge:** High point density on dense road grids caused "jitter" — routes crossing between parallel roads.

**Solution:** Implemented **Distance-Proportional Radius** and **Multi-Rotation Fitting**. Dynamically spreading points based on total route length provides enough "slack" for the router to stay on a single path.

### Loop Closure
**Challenge:** Shapes often start and end at different points in SVG space — runners need to return home!

**Solution:** Our scoring engine penalizes "open" routes. It calculates the Euclidean gap between start/end nodes after road-snapping and heavily weights loop closure in the final score.

---

## Accomplishments We're Proud Of

- ✅ End-to-end shape-to-route in under 3 seconds
- ✅ Seamless 4-mode input system (Prompt → Draw → Text → Upload)
- ✅ Production-ready GPX export compatible with major fitness platforms
- ✅ Self-hosted routing infrastructure handling high concurrency

---

## What We Learned

- OSRM's flexibility with custom Lua profiles is incredible for niche use cases
- Geometric constraints (like perimeter preservation) require careful math to feel intuitive to users
- LLM-powered shape suggestion works best with RAG over a curated icon library

---

## What's Next

- 🌍 Expand beyond Singapore to global coverage
- 🏃 Add pace/elevation preferences for route optimization
- 🎯 Collaborative "challenge" mode — race friends on identical shapes
- 📱 Native mobile app with real-time GPS tracking

---

## Built With

`nextjs` `react` `typescript` `python` `fastapi` `osrm` `leaflet` `gemini` `potrace` `freetype` `docker`

---

## Try It Out

🔗 **Live Demo:** [Coming Soon]  
📦 **GitHub:** [github.com/your-repo/drawmyroute](https://github.com/your-repo/drawmyroute)
