const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RouteRequest {
  shape_id?: string;
  prompt?: string;
  start_lat: number;
  start_lng: number;
  distance_km: number;
  aspect_ratio?: number;  // >1 = taller, <1 = wider (0.25-4.0)
  fast_mode?: boolean;    // Skip multi-variant optimization for faster resize
}

export interface RouteResponse {
  shape_id: string;
  shape_name: string;
  svg_path: string;
  route: GeoJSON.LineString;
  distance_m: number;
  duration_s: number;
  original_points?: number[][];
  gps_points?: number[][];
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

