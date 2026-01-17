"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import RouteResizeOverlay from "./RouteResizeOverlay";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";
const STRAVA_ORANGE = "#FC4C02";

interface MapComponentProps {
  route?: GeoJSON.LineString | null;
  center?: [number, number]; // [lng, lat]
  onResize?: (aspectRatio: number) => void;
  onMove?: (newLat: number, newLng: number) => void;
  isResizing?: boolean;
  svgPath?: string | null;
  showOverlay?: boolean;
}

export default function MapComponent({ route, center, onResize, onMove, isResizing = false, svgPath, showOverlay = true }: MapComponentProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const marker = useRef<mapboxgl.Marker | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [routeBounds, setRouteBounds] = useState<{
    minLng: number;
    maxLng: number;
    minLat: number;
    maxLat: number;
  } | null>(null);

  // 1. Initialize map (RUNS ONLY ONCE)
  useEffect(() => {
    if (map.current) return;
    if (!mapContainer.current) return;

    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === "pk.YOUR_TOKEN_HERE") {
      console.warn("Mapbox token is missing");
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: "mapbox://styles/mapbox/streets-v11",
        center: center || [103.8198, 1.3521], // Singapore default
        zoom: 13,
      });

      map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
      
      map.current.on("load", () => setMapLoaded(true));
    } catch (e) {
      console.error("Error initializing map:", e);
    }

    // Cleanup on unmount only
    return () => {
      if (marker.current) {
        marker.current.remove();
        marker.current = null;
      }
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []); // Empty dependency array = mount once

  // 2. Handle Center Updates (Fly to new location + update marker)
  useEffect(() => {
    if (!map.current || !center) return;

    // Update or create marker for starting location
    if (marker.current) {
      marker.current.setLngLat(center);
    } else {
      // Create custom marker element
      const el = document.createElement("div");
      el.innerHTML = `
        <div style="
          width: 24px;
          height: 24px;
          background: ${STRAVA_ORANGE};
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          cursor: pointer;
        "></div>
      `;
      
      marker.current = new mapboxgl.Marker({ element: el, anchor: "center" })
        .setLngLat(center)
        .setPopup(new mapboxgl.Popup({ offset: 25 }).setText("Start Location"))
        .addTo(map.current);
    }

    // Only fly if the distance is significant to avoid jitter
    const currentCenter = map.current.getCenter();
    const dist = Math.sqrt(
      Math.pow(currentCenter.lng - center[0], 2) +
        Math.pow(currentCenter.lat - center[1], 2)
    );

    if (dist > 0.0001) {
      map.current.flyTo({
        center: center,
        zoom: 14,
        essential: true,
      });
    }
  }, [center ? center[0] : null, center ? center[1] : null]); // Depend on primitives, not array ref

  // 3. Draw Route (Update Source/Layer)
  useEffect(() => {
    if (!map.current || !route) return;

    const drawRoute = () => {
      if (!map.current) return;

      // Calculate route bounds for resize overlay
      const coordinates = route.coordinates as [number, number][];
      if (coordinates.length > 0) {
        const lngs = coordinates.map(c => c[0]);
        const lats = coordinates.map(c => c[1]);
        setRouteBounds({
          minLng: Math.min(...lngs),
          maxLng: Math.max(...lngs),
          minLat: Math.min(...lats),
          maxLat: Math.max(...lats),
        });
      }

      // Remove existing route if any
      if (map.current.getSource("route")) {
        // Just update data if source exists
        (map.current.getSource("route") as mapboxgl.GeoJSONSource).setData({
          type: "Feature",
          properties: {},
          geometry: route,
        });
      } else {
        // Add source and layers if new
        map.current.addSource("route", {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: route,
          },
        });

        // Add outline layer (for better visibility)
        map.current.addLayer({
          id: "route-outline",
          type: "line",
          source: "route",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": "#fff",
            "line-width": 8,
            "line-opacity": 0.8,
          },
        });

        // Add main route layer
        map.current.addLayer({
          id: "route-line",
          type: "line",
          source: "route",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": STRAVA_ORANGE,
            "line-width": 5,
            "line-opacity": 1,
          },
        });
      }

      // Fit map to route bounds (skip during resize/move to prevent zoom)
      if (coordinates.length > 0 && !isResizing) {
        const bounds = coordinates.reduce(
          (bounds, coord) => bounds.extend(coord),
          new mapboxgl.LngLatBounds(coordinates[0], coordinates[0])
        );

        map.current.fitBounds(bounds, {
          padding: 80,
          duration: 1000,
        });
      }
    };

    // Wait for map to be loaded
    if (map.current.isStyleLoaded()) {
      drawRoute();
    } else {
      map.current.once("load", drawRoute);
    }
  }, [route]);

  // Handle resize from overlay
  const handleOverlayResize = useCallback((aspectRatioMultiplier: number) => {
    if (onResize) {
      onResize(aspectRatioMultiplier);
    }
  }, [onResize]);

  // Handle move from overlay
  const handleOverlayMove = useCallback((newLat: number, newLng: number) => {
    if (onMove) {
      onMove(newLat, newLng);
    }
  }, [onMove]);

  return (
    <div ref={mapContainer} className="w-full h-full" style={{ position: "relative" }}>
      {mapLoaded && route && onResize && showOverlay && (
        <RouteResizeOverlay
          bounds={routeBounds}
          mapRef={map.current}
          onResize={handleOverlayResize}
          onMove={onMove ? handleOverlayMove : undefined}
          disabled={isResizing}
          svgPath={svgPath}
        />
      )}
    </div>
  );
}
