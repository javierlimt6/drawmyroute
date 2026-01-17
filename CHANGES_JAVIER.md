# DrawMyRoute - Javier's Changes Log

## 2026-01-17

### Frontend Setup
- Initialized Next.js 16+ project with TypeScript and Tailwind CSS
- Installed dependencies: `mapbox-gl`, `antd`, `@ant-design/icons`, `lucide-react`, `clsx`
- Created Mapbox map component (`src/components/Map.tsx`)
- Created geolocation hook (`src/hooks/use-location.tsx`)

### UI Implementation
- Built centered landing modal with:
  - Location search input with GPS button
  - Type/Draw mode toggle (Segmented)
  - Prompt text area with character count
  - Distance slider (1-20 km)
  - Generate Route CTA button
- Applied Strava theming:
  - Primary color: `#FC4C02` (Strava Orange)
  - Dark header: `#1A1A1A`
  - Bold typography and athletic styling

### Branding
- Renamed from "PathArt" to "DrawMyRoute"
- Added Hack&Roll 2026 subtitle with "duo showdown" team credit
- Added GitHub link in header → `github.com/javierlimt6/drawmyroute`
- Updated page title and meta description

### Pending
- [x] Predefined shapes visual selector
- [x] Loading state during generation
- [x] Route visualization on map
- [ ] Backend API integration (using mock data currently)
