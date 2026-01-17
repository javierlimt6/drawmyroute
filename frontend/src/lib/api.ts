const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RouteRequest {
  shape_id?: string;
  prompt?: string;
  start_lat: number;
  start_lng: number;
  distance_km: number;
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
