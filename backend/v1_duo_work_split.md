# DrawMyRoute V1 - Duo Work Split (Balanced)

## Current State

| Component | Status |
|-----------|--------|
| Frontend UI | ✅ Complete (mock data) |
| Backend API | ⚠️ 3/8 shapes |
| Integration | ❌ Not connected |

---

## Builder A: 3 Shapes + Frontend API (~50 min)

| Task | Area | Time |
|------|------|------|
| Add circle, figure8, lightning to `shapes.json` | Backend | 10 min |
| Test 3 shapes with curl | Backend | 10 min |
| Create `lib/api.ts` | Frontend | 10 min |
| Connect page.tsx to real API | Frontend | 15 min |
| Add error handling UI | Frontend | 5 min |

### Shapes to Add
```json
"circle": { "name": "Circle", "svg_path": "M 50 0 A 50 50 0 1 1 50 100 A 50 50 0 1 1 50 0 Z" },
"figure8": { "name": "Figure 8", "svg_path": "M 50 25 C 75 0, 100 25, 75 50 C 100 75, 75 100, 50 75 C 25 100, 0 75, 25 50 C 0 25, 25 0, 50 25 Z" },
"lightning": { "name": "Lightning", "svg_path": "M 40 0 L 60 0 L 55 35 L 80 35 L 30 100 L 40 55 L 20 55 Z" }
```

---

## Builder B: 2 Shapes + Backend Polish (~50 min)

| Task | Area | Time |
|------|------|------|
| Add singapore, merlion to `shapes.json` | Backend | 10 min |
| Add error handling to API | Backend | 10 min |
| CORS for production URL | Backend | 5 min |
| Write backend README | Docs | 10 min |
| Test all 8 shapes end-to-end | Backend | 15 min |

### Shapes to Add
```json
"singapore": { "name": "Singapore", "svg_path": "M 10 50 L 30 30 L 50 35 L 70 25 L 90 40 L 85 60 L 60 70 L 40 65 L 20 70 Z" },
"merlion": { "name": "Merlion", "svg_path": "M 50 10 L 60 30 L 80 35 L 70 50 L 75 70 L 50 90 L 25 70 L 30 50 L 20 35 L 40 30 Z" }
```

---

## Integration (~20 min)

| Step | Who | Task |
|------|-----|------|
| 1 | Both | Merge shapes into single `shapes.json` |
| 2 | B | Start backend: `uvicorn app.main:app --reload` |
| 3 | A | Set `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| 4 | Both | Test all 8 shapes end-to-end |

---

## API Contract

```typescript
// POST /api/v1/generate
Request: { shape_id, start_lat, start_lng, distance_km }
Response: { shape_id, shape_name, route: GeoJSON.LineString, distance_m, duration_s }
```

---

## Timeline

```
Builder A                    Builder B
─────────────────────────    ─────────────────────────
[3 shapes → shapes.json]     [2 shapes → shapes.json]
[lib/api.ts + page.tsx]      [Error handling + CORS]
[Error handling UI]          [README + Test all]
─────────────────────────────────────────────────────
              INTEGRATION (Both) ~20 min
─────────────────────────────────────────────────────
              TOTAL: ~2 hours
```
