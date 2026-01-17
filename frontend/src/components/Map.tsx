"use client";

import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

export default function MapComponent() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (map.current) return; // initialize map only once
    if (!mapContainer.current) return;

    // Fix for missing access token if not set
    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === 'pk.YOUR_TOKEN_HERE') {
      console.warn("Mapbox token is missing");
      // We still try to init, mapbox will error if token invalid
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [103.8198, 1.3521], // Singapore
        zoom: 11
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
  }, []);

  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}
