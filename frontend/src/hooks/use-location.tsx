"use client";

import { useState, useCallback } from 'react';

interface LocationState {
  latitude: number | null;
  longitude: number | null;
  error: string | null;
  loading: boolean;
  isManual: boolean;
}

export function useLocation() {
  const [location, setLocation] = useState<LocationState>({
    latitude: null,
    longitude: null,
    error: null,
    loading: false,
    isManual: false,
  });

  const getCurrentLocation = useCallback(() => {
    setLocation(prev => ({ ...prev, loading: true, error: null }));

    if (!navigator.geolocation) {
      setLocation(prev => ({ 
        ...prev, 
        loading: false, 
        error: "Geolocation is not supported by your browser" 
      }));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          error: null,
          loading: false,
          isManual: false,
        });
      },
      (error) => {
        setLocation(prev => ({ 
          ...prev, 
          loading: false, 
          error: error.message 
        }));
      }
    );
  }, []);

  const setManualLocation = useCallback((lat: number, lng: number) => {
    setLocation({
      latitude: lat,
      longitude: lng,
      error: null,
      loading: false,
      isManual: true,
    });
  }, []);

  return { ...location, getCurrentLocation, setManualLocation };
}
