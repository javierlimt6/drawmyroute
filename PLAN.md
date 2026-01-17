# Updated Technical Design: PathArt (AI-Powered)

## 1. The "Prompt-to-Path" Flow

This is the heart of your AI integration.

1. **Input:** User types "A running route in the shape of a coffee mug" on the **Frontend**.
2. **Request:** Frontend sends this string to the **Backend**.
3. **AI Processing:** Backend calls Gemini/GPT-4o with a system prompt to return a **normalized SVG path**.
4. **Parsing:** Backend uses `svg.path` (Python) to sample the path into 20-30 discrete $(x, y)$ coordinates.
5. **Scaling:** Backend scales these points based on the user's requested distance (e.g., 5km) and starting GPS.
6. **Snapping:** Backend sends these GPS points to **Mapbox Map Matching API** to align them with Singapore's roads/park connectors.
7. **Output:** Backend returns a GeoJSON to the **Frontend** to render on the map.

---

## 2. Team Division & Detailed Flow

### **Builder 1: Frontend (React/Next.js)**

**Focus:** UI, Map Rendering, and User Input.

- **Setup (H 0-4):**
    - Initialize Next.js and integrate **Mapbox GL JS**.
    - Create a "Draw/Type" toggle.
    - Implement the "Start Location" picker (using Geolocation API).
- **Integration (H 4-12):**
    - Build the text input for the AI Prompt.
    - Create a loading state (crucial for AI/Map Matching latency).
    - Handle the GeoJSON response: Render the "snapped" route and the "original" shape as a faint overlay.
- **Polish (H 12-24):**
    - Add "Route Stats" (Total KM, Estimated Time, Elevation).
    - Implement a "Share" feature (generate a PNG/screenshot of the route).

### **Builder 2: Backend (FastAPI/Python)**

**Focus:** AI Orchestration and Geometry Math.

- **Setup (H 0-4):**
    - FastAPI boilerplate with CORS enabled for the frontend.
    - Set up OpenAI/Gemini API and Mapbox API keys.
- **The AI Engine (H 4-12):**
    - **The Prompt:** Write the system prompt to force the LLM to return *only* SVG path data.
    - **The Parser:** Use `svg.path` to convert the `d=` string into a list of points.
    - **The Scaler:** Write the function to transform $100 \times 100$ coordinates into Lat/Long based on a distance $D$.
- **The Map Engine (H 12-18):**
    - Connect to Mapbox Map Matching.
    - Handle "failed" matches (e.g., if the shape goes into the sea, offset the starting point and retry).
- **Optimization (H 18-24):**
    - Caching: If someone asks for a "Heart," cache the coordinates so you don't call the LLM twice.

---

## 3. High-Value AI System Prompt

*To be used by the Backend developer in the API call:*

> "You are a geometric assistant. The user wants a map route in the shape of: {USER_INPUT}.
> 
> 
> Generate a simplified SVG path 'd' attribute.
> 
> Constraints:
> 
> 1. Coordinate system: 0,0 to 100,100.
> 2. The path must be closed (end with Z).
> 3. Use minimal points (max 25) to ensure map matching works.
> 4. Return ONLY the path string. No text, no markdown."

---

## 4. 24-Hour "Hack & Roll" Timeline

| **Time** | **Frontend (Builder 1)** | **Backend (Builder 2)** |
| --- | --- | --- |
| **10:00 PM (Start)** | Mapbox setup & UI Mockup | API setup & LLM Prompt testing |
| **02:00 AM** | Location picking & Draw tool | SVG $\rightarrow$ Coordinate parsing logic |
| **06:00 AM** | **Sync:** Connect FE to BE | **Sync:** Finalize scaling logic |
| **10:00 AM** | Route visualization & Overlays | Map Matching API integration |
| **02:00 PM** | UI Polish & Animations | Error handling & Edge cases |
| **06:00 PM** | Demo Recording & Pitch Deck | Final Deployment |
| **10:00 PM (End)** | **SUBMISSION** | **SUBMISSION** |

---

## 5. Potential Pitfalls to Watch For

- **The "Water" Problem:** Since you're in Singapore, a 5km "Elephant" shape might end up in the Kallang Basin.
    - *Solution:* Add a basic check in the Backend—if more than 50% of the points are in water, shift the center point inland.
- **Token Latency:** LLM calls take 2-4 seconds. Map Matching takes 1-2 seconds.
    - *Solution:* Use a funny "drawing your route..." skeleton loader on the Frontend to keep the user engaged.

**Would you like me to generate the Python code for the `svg_to_lat_long` scaling function to save your backend builder some time?**