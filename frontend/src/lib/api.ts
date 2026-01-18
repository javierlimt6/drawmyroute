const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RouteRequest {
  shape_id?: string;
  prompt?: string;
  text?: string;  // Text to convert to route shape (e.g., "NUS", "67")
  image_svg_path?: string;  // SVG path from uploaded image
  start_lat: number;
  start_lng: number;
  distance_km: number;
  aspect_ratio?: number;  // >1 = taller, <1 = wider (0.25-4.0)
  fast_mode?: boolean;    // Skip multi-variant optimization for faster resize
  adaptive_resize?: boolean;  // Enable adaptive height calculation for width changes
  width_ratio?: number;   // How much width changed (>1 = wider)
}

export interface RouteResponse {
  shape_id: string;
  shape_name: string;
  input_prompt?: string;
  svg_path: string;
  route: GeoJSON.LineString;
  distance_m: number;
  original_points?: number[][];
  gps_points?: number[][];
  rotation_deg?: number; // Added for overlay rotation
}

export interface ParseImageResponse {
  svg_path: string;
}

export async function parseImage(file: File): Promise<ParseImageResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/api/v1/parse-image`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function generateRoute(request: RouteRequest): Promise<RouteResponse> {
  const res = await fetch(`${API_URL}/api/v1/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function getShapes(): Promise<Record<string, { name: string; svg_path: string }>> {
  const res = await fetch(`${API_URL}/api/v1/shapes`);
  if (!res.ok) throw new Error("Failed to fetch shapes");
  return res.json();
}

export async function exportGPX(request: RouteRequest): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/export/gpx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  // Get filename from Content-Disposition header or use default
  const contentDisposition = res.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : "drawmyroute.gpx";

  // Download the file
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export interface SuggestRequest {
  start_lat: number;
  start_lng: number;
  distance_km: number;
  num_candidates?: number;  // Default 10
  aspect_ratio?: number;
}

export interface SuggestResponse extends RouteResponse {
  suggestion_metadata?: {
    candidates_tried: number;
    candidates_passed: number;
    alternatives: { name: string; score: number }[];
  };
}

export async function suggestRoute(request: SuggestRequest): Promise<SuggestResponse> {
  const res = await fetch(`${API_URL}/api/v1/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
