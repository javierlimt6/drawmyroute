"use client";

import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";
const STRAVA_ORANGE = "#FC4C02";

interface MapComponentProps {
  route?: GeoJSON.LineString | null;
  center?: [number, number]; // [lng, lat]
}

export default function MapComponent({ route, center }: MapComponentProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  // Initialize map
  useEffect(() => {
    if (map.current) return;
    if (!mapContainer.current) return;

    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === 'pk.YOUR_TOKEN_HERE') {
      console.warn("Mapbox token is missing");
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: center || [103.8198, 1.3521], // Singapore default
        zoom: 13
      });

      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    } catch (e) {
      console.error("Error initializing map:", e);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [center]);

  // Draw route when it changes
  useEffect(() => {
    if (!map.current || !route) return;

    const drawRoute = () => {
      if (!map.current) return;

      // Remove existing route if any
      if (map.current.getSource('route')) {
        map.current.removeLayer('route-line');
        map.current.removeLayer('route-outline');
        map.current.removeSource('route');
      }

      // Add route source
      map.current.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: route
        }
      });

      // Add outline layer (for better visibility)
      map.current.addLayer({
        id: 'route-outline',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#fff',
          'line-width': 8,
          'line-opacity': 0.8
        }
      });

      // Add main route layer
      map.current.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': STRAVA_ORANGE,
          'line-width': 5,
          'line-opacity': 1
        }
      });

      // Fit map to route bounds
      const coordinates = route.coordinates as [number, number][];
      const bounds = coordinates.reduce(
        (bounds, coord) => bounds.extend(coord),
        new mapboxgl.LngLatBounds(coordinates[0], coordinates[0])
      );

      map.current.fitBounds(bounds, {
        padding: 80,
        duration: 1000
      });
    };

    // Wait for map to be loaded
    if (map.current.isStyleLoaded()) {
      drawRoute();
    } else {
      map.current.on('load', drawRoute);
    }
  }, [route]);

  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}
