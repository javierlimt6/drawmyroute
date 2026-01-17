/**
 * Geocoding utilities using OpenStreetMap's Nominatim API (free, no API key required)
 */

export interface GeocodingResult {
  display_name: string;
  lat: number;
  lon: number;
  type: string;
  importance: number;
}

export interface GeocodingError {
  message: string;
}

const NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org";

/**
 * Search for locations matching a query string
 */
export async function searchLocations(query: string): Promise<GeocodingResult[]> {
  if (!query.trim()) {
    return [];
  }

  try {
    const params = new URLSearchParams({
      q: query,
      format: "json",
      limit: "5",
      addressdetails: "1",
    });

    const response = await fetch(`${NOMINATIM_BASE_URL}/search?${params}`, {
      headers: {
        "User-Agent": "DrawMyRoute/1.0 (Hack&Roll 2026)",
      },
    });

    if (!response.ok) {
      throw new Error(`Geocoding failed: ${response.statusText}`);
    }

    const data = await response.json();
    
    return data.map((item: {
      display_name: string;
      lat: string;
      lon: string;
      type: string;
      importance: number;
    }) => ({
      display_name: item.display_name,
      lat: parseFloat(item.lat),
      lon: parseFloat(item.lon),
      type: item.type,
      importance: item.importance,
    }));
  } catch (error) {
    console.error("Geocoding error:", error);
    throw error;
  }
}

/**
 * Reverse geocode coordinates to get a human-readable address
 */
export async function reverseGeocode(lat: number, lon: number): Promise<string> {
  try {
    const params = new URLSearchParams({
      lat: lat.toString(),
      lon: lon.toString(),
      format: "json",
    });

    const response = await fetch(`${NOMINATIM_BASE_URL}/reverse?${params}`, {
      headers: {
        "User-Agent": "DrawMyRoute/1.0 (Hack&Roll 2026)",
      },
    });

    if (!response.ok) {
      throw new Error(`Reverse geocoding failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.display_name || "Unknown location";
  } catch (error) {
    console.error("Reverse geocoding error:", error);
    return "Unknown location";
  }
}
