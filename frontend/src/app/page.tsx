"use client";

import MapComponent from "@/components/Map";
import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation } from "@/hooks/use-location";
import { generateRoute, exportGPX, parseImage, suggestRoute } from "@/lib/api";
import {
  searchLocations,
  reverseGeocode,
  GeocodingResult,
} from "@/lib/geocoding";
import {
  Card,
  Typography,
  Input,
  Button,
  Space,
  ConfigProvider,
  Segmented,
  Slider,
  Alert,
  AutoComplete,
} from "antd";
import {
  EnvironmentOutlined,
  SearchOutlined,
  LoadingOutlined,
  AimOutlined,
  EditOutlined,
  FontSizeOutlined,
  RocketOutlined,
  DownloadOutlined,
  UploadOutlined,
  PictureOutlined,
} from "@ant-design/icons";

const { Title, Text } = Typography;
const { TextArea } = Input;

// Strava brand colors
const STRAVA_ORANGE = "#FC4C02";
const STRAVA_DARK = "#1A1A1A";

// Feature toggles
const SHOW_QUICK_SELECT_SHAPES = false; // Set to false to hide quick select shapes

type InputMode = "type" | "draw" | "text" | "image";

interface PredefinedShape {
  id: string;
  name: string;
  emoji: string;
  prompt: string;
}

const PREDEFINED_SHAPES: PredefinedShape[] = [
  {
    id: "heart",
    name: "Heart",
    emoji: "❤️",
    prompt: "A route shaped like a heart",
  },
  {
    id: "star",
    name: "Star",
    emoji: "⭐",
    prompt: "A route shaped like a 5-point star",
  },
  {
    id: "circle",
    name: "Circle",
    emoji: "⭕",
    prompt: "A circular loop route",
  },
  {
    id: "square",
    name: "Square",
    emoji: "⬜",
    prompt: "A route shaped like a square",
  },
  {
    id: "triangle",
    name: "Triangle",
    emoji: "🔺",
    prompt: "A route shaped like a triangle",
  },
  {
    id: "sixty7",
    name: "67",
    emoji: "6️⃣7️⃣",
    prompt: "A route shaped like the number 67",
  },
  {
    id: "figure8",
    name: "Figure 8",
    emoji: "♾️",
    prompt: "A route shaped like a figure 8",
  },
  {
    id: "lightning",
    name: "Lightning",
    emoji: "⚡",
    prompt: "A route shaped like a lightning bolt",
  },
  {
    id: "dinosaur",
    name: "Dinosaur",
    emoji: "🦖",
    prompt: "A route shaped like a T-Rex dinosaur",
  },
  {
    id: "singapore",
    name: "SG",
    emoji: "🇸🇬",
    prompt: "A route shaped like Singapore's outline",
  },
  {
    id: "merlion",
    name: "Merlion",
    emoji: "🦁",
    prompt: "A route shaped like the Merlion",
  },
  {
    id: "banana",
    name: "Banana",
    emoji: "🍌",
    prompt: "A route shaped like a banana",
  },
  {
    id: "snowflake",
    name: "Snowflake",
    emoji: "❄️",
    prompt: "A route shaped like a snowflake",
  },
  {
    id: "thumbsup",
    name: "Thumbs Up",
    emoji: "👍",
    prompt: "A route shaped like a thumbs up",
  },
  {
    id: "sword",
    name: "Sword",
    emoji: "⚔️",
    prompt: "A route shaped like a sword",
  },
];

export default function Home() {
  const [showModal, setShowModal] = useState(true);
  const [mode, setMode] = useState<InputMode>("type");
  const [prompt, setPrompt] = useState("");
  const [textInput, setTextInput] = useState("");  // Text mode input (e.g., "NUS", "67")
  const [selectedShape, setSelectedShape] = useState<string | null>(null);
  const [distance, setDistance] = useState(25); // Always stored in km
  const [unit, setUnit] = useState<"km" | "mi">("km");
  // targetPace removed
  const [searchValue, setSearchValue] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRoute, setGeneratedRoute] =
    useState<GeoJSON.LineString | null>(null);
  const [generatedSvg, setGeneratedSvg] = useState<string | null>(null);
  const [inputPrompt, setInputPrompt] = useState<string | null>(null);
  const [rotationDeg, setRotationDeg] = useState<number>(0);
  const [aspectRatio, setAspectRatio] = useState(1.0); // For interactive resize
  const [routeCenter, setRouteCenter] = useState<{
    lat: number;
    lng: number;
  } | null>(null); // Separate from orange dot
  const [routeStats, setRouteStats] = useState<{
    distance_m: number;
  } | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);  // Toggle for resize overlay
  const [imageSvgPath, setImageSvgPath] = useState<string | null>(null);  // SVG path from uploaded image
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);  // Auto-suggest loading state
  const {
    latitude,
    longitude,
    loading: locationLoading,
    isManual,
    getCurrentLocation,
    setManualLocation,
  } = useLocation();

  // Update search box when location is found via GPS
  useEffect(() => {
    if (latitude && longitude && !isManual && !searchValue) {
      setSearchValue(
        `Current Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`
      );
    }
  }, [latitude, longitude, isManual, searchValue]);

  // Geocoding state
  const [searchOptions, setSearchOptions] = useState<
    { value: string; label: string; data: GeocodingResult }[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced search for geocoding
  const handleSearchChange = useCallback((value: string) => {
    setSearchValue(value);

    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!value.trim()) {
      setSearchOptions([]);
      return;
    }

    // Debounce the search
    searchTimeoutRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchLocations(value);
        setSearchOptions(
          results.map((result) => ({
            value: result.display_name,
            label: result.display_name,
            data: result,
          }))
        );
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 800); // Reduced to 800ms for snappier feel
  }, []);

  // Handle selecting a location from autocomplete
  const handleLocationSelect = useCallback(
    (
      value: string,
      option: { value: string; label: string; data: GeocodingResult }
    ) => {
      setSearchValue(value);
      setManualLocation(option.data.lat, option.data.lon);
    },
    [setManualLocation]
  );

  // When using GPS, update the search field with the address
  const handleGetCurrentLocation = useCallback(async () => {
    getCurrentLocation();
  }, [getCurrentLocation]);

  // Reverse geocode when GPS location is obtained
  useEffect(() => {
    if (latitude && longitude && !isManual && !searchValue) {
      reverseGeocode(latitude, longitude).then((address) => {
        setSearchValue(address);
      });
    }
  }, [latitude, longitude, isManual, searchValue]);

  // Conversion helpers
  const KM_TO_MI = 0.621371;
  const MI_TO_KM = 1.60934;

  const displayDistance = unit === "km" ? distance : distance * KM_TO_MI;
  const setDistanceFromDisplay = (val: number) => {
    setDistance(unit === "km" ? val : val * MI_TO_KM);
  };

  // Real API call
  const handleGenerate = async () => {
    let lat = latitude;
    let lng = longitude;

    // If no location, get it first
    if (!lat || !lng) {
      setIsGenerating(true);
      try {
        const position = await new Promise<GeolocationPosition>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              timeout: 10000,
            });
          }
        );
        lat = position.coords.latitude;
        lng = position.coords.longitude;
        setManualLocation(lat, lng);
        setSearchValue(
          `Current Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`
        );
      } catch (err) {
        setError("Could not get location. Please enter an address.");
        setIsGenerating(false);
        return;
      }
    }

    setIsGenerating(true);
    setError(null);

    try {
      const requestPayload = {
        start_lat: lat,
        start_lng: lng,
        distance_km: distance,
        aspect_ratio: aspectRatio,
        ...(mode === "image" && imageSvgPath
          ? { image_svg_path: imageSvgPath }
          : mode === "type" && prompt.trim()
          ? { prompt: prompt.trim() }
          : mode === "text" && textInput.trim()
          ? { text: textInput.trim() }
          : { shape_id: selectedShape || "heart" }),
      };

      const result = await generateRoute(requestPayload);

      setGeneratedRoute(result.route);
      setGeneratedSvg(result.svg_path);
      setInputPrompt(result.input_prompt || null);
      setRotationDeg(result.rotation_deg ?? 0);
      console.log("Backend rotation_deg:", result.rotation_deg);
      setRouteStats({
        distance_m: result.distance_m,
      });
      setShowModal(false);
    } catch (err) {
      console.error("Generation failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate route. Try a different location or shape."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSuggest = async () => {
    let lat = latitude;
    let lng = longitude;
    
    // If no location, get it first
    if (!lat || !lng) {
      setIsSuggesting(true);
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
        });
        lat = position.coords.latitude;
        lng = position.coords.longitude;
        setManualLocation(lat, lng);
        setSearchValue(`Current Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
      } catch (err) {
        setError("Could not get location. Please enter an address.");
        setIsSuggesting(false);
        return;
      }
    }

    setIsSuggesting(true);
    setError(null);

    try {
      const result = await suggestRoute({
        start_lat: lat,
        start_lng: lng,
        distance_km: distance,
        num_candidates: 10,
        aspect_ratio: aspectRatio,
      });

      setGeneratedRoute(result.route);
      setGeneratedSvg(result.svg_path);
      setInputPrompt(result.shape_name || null);  // Store for display
      setRotationDeg(result.rotation_deg ?? 0);
      
      // CRITICAL: Store svg_path and set mode to 'image' so move/resize uses the same SVG
      setImageSvgPath(result.svg_path);
      setMode("image");
      
      // Clear other inputs to prevent them from overriding on move/resize
      setTextInput("");
      setPrompt("");
      setSelectedShape(null);
      
      setRouteStats({
        distance_m: result.distance_m,
      });
      setShowModal(false);
    } catch (err) {
      console.error("Suggestion failed:", err);
      setError(err instanceof Error ? err.message : "Failed to suggest route. Try a different location.");
    } finally {
      setIsSuggesting(false);
    }
  };

  // Debounced resize - only triggers API after user stops dragging
  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Bounds type for resize
  interface ResizeBounds {
    minLat: number;
    maxLat: number;
    minLng: number;
    maxLng: number;
  }
  
  const handleResize = (newBounds: ResizeBounds) => {
    // Clear previous timeout
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }

    // Store previous state for revert
    const prevRoute = generatedRoute;
    const prevStats = routeStats;

    // Debounce: wait 300ms after last drag before calling API
    resizeTimeoutRef.current = setTimeout(async () => {
      setIsGenerating(true);
      try {
        // Build request with target_bounds (authoritative box dimensions)
        const requestPayload = {
          start_lat: (newBounds.minLat + newBounds.maxLat) / 2,  // Center for fallback
          start_lng: (newBounds.minLng + newBounds.maxLng) / 2,
          distance_km: distance,  // Used for point count estimation
          fast_mode: true,  // Use fast mode for resize
          target_bounds: {
            min_lat: newBounds.minLat,
            max_lat: newBounds.maxLat,
            min_lng: newBounds.minLng,
            max_lng: newBounds.maxLng,
          },
          ...(mode === "image" && imageSvgPath
            ? { image_svg_path: imageSvgPath }
            : mode === "type" && prompt.trim()
            ? { prompt: prompt.trim() }
            : mode === "text" && textInput.trim()
            ? { text: textInput.trim() }
            : { shape_id: selectedShape || "heart" }),
        };

        const result = await generateRoute(requestPayload);
        setGeneratedRoute(result.route);
        setGeneratedSvg(result.svg_path);
        setInputPrompt(result.input_prompt || null);
        setRotationDeg(result.rotation_deg ?? 0);
        console.log("Backend rotation_deg:", result.rotation_deg);
        setRouteStats({
          distance_m: result.distance_m,
        });
        
        // Update route center to bounds center
        setRouteCenter({
          lat: (newBounds.minLat + newBounds.maxLat) / 2,
          lng: (newBounds.minLng + newBounds.maxLng) / 2,
        });
      } catch (err) {
        console.error("Resize failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to resize route. The area may not have enough roads."
        );
        // Revert to previous state
        setGeneratedRoute(prevRoute);
        setRouteStats(prevStats);
      } finally {
        setIsGenerating(false);
      }
    }, 300);
  };

  // Handle move - regenerate route at new location (does NOT update orange dot)
  const moveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const previousRouteCenterRef = useRef<{ lat: number; lng: number } | null>(
    null
  );

  const handleMove = (newLat: number, newLng: number) => {
    // Store previous route center for revert on error
    previousRouteCenterRef.current =
      routeCenter ??
      (latitude && longitude ? { lat: latitude, lng: longitude } : null);

    // Update route center (does NOT affect orange dot or search value)
    setRouteCenter({ lat: newLat, lng: newLng });

    // Clear previous timeout
    if (moveTimeoutRef.current) {
      clearTimeout(moveTimeoutRef.current);
    }

    // Store previous state for revert
    const prevRoute = generatedRoute;
    const prevStats = routeStats;

    // Debounce: wait 300ms before calling API
    moveTimeoutRef.current = setTimeout(async () => {
      setIsGenerating(true);
      try {
        const requestPayload = {
          start_lat: newLat,
          start_lng: newLng,
          distance_km: distance,
          aspect_ratio: aspectRatio,
          fast_mode: true,
          ...(mode === "image" && imageSvgPath
            ? { image_svg_path: imageSvgPath }
            : mode === "type" && prompt.trim()
            ? { prompt: prompt.trim() }
            : mode === "text" && textInput.trim()
            ? { text: textInput.trim() }
            : { shape_id: selectedShape || "heart" }),
        };

        const result = await generateRoute(requestPayload);
        setGeneratedRoute(result.route);
        setGeneratedSvg(result.svg_path);
        setInputPrompt(result.input_prompt || null);
        setRotationDeg(result.rotation_deg ?? 0);
        console.log("Backend rotation_deg:", result.rotation_deg);
        setRouteStats({
          distance_m: result.distance_m,
        });
      } catch (err) {
        console.error("Move failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to move route. The area may not have enough roads."
        );
        // Revert to previous state
        setRouteCenter(previousRouteCenterRef.current);
        setGeneratedRoute(prevRoute);
        setRouteStats(prevStats);
      } finally {
        setIsGenerating(false);
      }
    }, 300);
  };
  const distanceMarks =
    unit === "km"
      ? { 0: "0", 10: "10", 20: "20", 30: "30", 40: "40", 50: "50" }
      : { 0: "0", 5: "5", 10: "10", 15: "15", 20: "20", 25: "25", 30: "30" };

  const sliderMax = unit === "km" ? 50 : 30;

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: STRAVA_ORANGE,
          borderRadius: 8,
          fontFamily:
            "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
      }}
    >
      <main className="relative w-full h-full min-h-screen">
        {/* Header */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 20,
            background: STRAVA_DARK,
          }}
        >
          {/* Single Consolidated Header */}
          <div
            style={{
              padding: "10px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            {/* Left - DrawMyRoute logo */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
                flexShrink: 0,
              }}
              onClick={() => {
                setShowModal(true);
                setGeneratedRoute(null);
                setGeneratedSvg(null);
                setInputPrompt(null);
                setRouteStats(null);
                setError(null);
                setAspectRatio(1.0);
              }}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill={STRAVA_ORANGE}
              >
                <path d="M12 2L4 20h5l3-6 3 6h5L12 2zm0 10l-1.5 3h3L12 12z" />
              </svg>
              <Text
                strong
                style={{ 
                  color: "#fff", 
                  fontSize: 16, 
                  letterSpacing: 0.5,
                  whiteSpace: "nowrap",
                }}
              >
                DrawMyRoute
              </Text>
            </div>

            {/* Center - Hack&Roll badge (hidden on small screens) */}
            <Text 
              style={{ color: "#888", fontSize: 11 }}
              className="hidden sm:block"
            >
              A Hack&Roll 2026 project by{" "}
              <span style={{ color: STRAVA_ORANGE }}>duo showdown</span>
            </Text>

            {/* Right - GitHub link */}
            <a
              href="https://github.com/javierlimt6/drawmyroute"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                color: "#888",
                fontSize: 13,
                textDecoration: "none",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              GitHub
            </a>
          </div>
        </div>

        {/* Map with overlay */}
        <div style={{ position: "relative", width: "100%", height: "100%", paddingTop: 48 }}>
          <MapComponent
            route={generatedRoute}
            center={longitude && latitude ? [longitude, latitude] : undefined}
            onResize={handleResize}
            onMove={handleMove}
            isResizing={isGenerating}
            svgPath={generatedSvg}
            showOverlay={showOverlay}
            rotationDeg={rotationDeg}
          />
          {showModal && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "rgba(0, 0, 0, 0.65)",
                zIndex: 5,
              }}
            />
          )}
        </div>

        {/* Centered Modal */}
        {showModal && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              padding: 16,
            }}
          >
            <Card
              style={{
                width: "100%",
                maxWidth: 400,
                maxHeight: "85vh",
                overflowY: "auto",
                borderRadius: 12,
                boxShadow: "0 12px 40px rgba(0,0,0,0.3)",
                border: "none",
              }}
              styles={{ body: { padding: "20px 24px" } }}
            >
              {/* Title - Compact */}
              <div style={{ textAlign: "center", marginBottom: 16 }}>
                <Title
                  level={4}
                  style={{ margin: 0, fontWeight: 700, color: STRAVA_DARK }}
                >
                  🗺️ DrawMyRoute
                </Title>
                <Text style={{ fontSize: 12, color: "#888" }}>
                  Create custom routes shaped to your imagination
                </Text>
              </div>

              {/* Location Search */}
              <div style={{ marginBottom: 20 }}>
                <AutoComplete
                  style={{ width: "100%" }}
                  options={searchOptions}
                  value={searchValue}
                  onSearch={handleSearchChange}
                  onSelect={handleLocationSelect}
                  notFoundContent={isSearching ? "Searching..." : null}
                >
                  <Input
                    size="large"
                    placeholder="Enter starting location..."
                    prefix={<SearchOutlined style={{ color: "#999" }} />}
                    suffix={
                      <Button
                        type="text"
                        size="small"
                        icon={
                          locationLoading || isSearching ? (
                            <LoadingOutlined spin />
                          ) : (
                            <AimOutlined />
                          )
                        }
                        onClick={handleGetCurrentLocation}
                        style={{ color: latitude ? "#52c41a" : STRAVA_ORANGE }}
                        title={
                          latitude ? "Location set" : "Use my current location"
                        }
                      />
                    }
                    style={{ borderRadius: 8, height: 48 }}
                  />
                </AutoComplete>
                {latitude && longitude && (
                  <Text
                    style={{
                      fontSize: 11,
                      color: "#52c41a",
                      marginTop: 4,
                      display: "block",
                    }}
                  >
                    <EnvironmentOutlined /> Location set: {latitude.toFixed(4)},{" "}
                    {longitude.toFixed(4)}
                  </Text>
                )}
              </div>

              {/* Predefined Shapes Selector */}
              {SHOW_QUICK_SELECT_SHAPES && (
              <>
              <div style={{ marginBottom: 16 }}>
                <Text
                  strong
                  style={{
                    display: "block",
                    marginBottom: 10,
                    color: STRAVA_DARK,
                  }}
                >
                  Quick Pick a Shape
                </Text>
                <div
                  style={{
                    display: "flex",
                    gap: 10,
                    overflowX: "auto",
                    paddingBottom: 8,
                    scrollbarWidth: "thin",
                  }}
                >
                  {PREDEFINED_SHAPES.map((shape) => (
                    <div
                      key={shape.id}
                      onClick={() => {
                        if (selectedShape === shape.id) {
                          setSelectedShape(null);
                          setPrompt("");
                        } else {
                          setSelectedShape(shape.id);
                          setPrompt(shape.prompt);
                          // Clear text input to prevent it from overriding the shape selection
                          setTextInput("");
                          // Reset mode if in text mode to ensure shape_id is used
                          if (mode === "text") {
                            setMode("type");
                          }
                        }
                      }}
                      style={{
                        minWidth: 72,
                        padding: "12px 8px",
                        borderRadius: 12,
                        border:
                          selectedShape === shape.id
                            ? `2px solid ${STRAVA_ORANGE}`
                            : "2px solid #eee",
                        background:
                          selectedShape === shape.id ? "#FFF5F0" : "#fff",
                        cursor: "pointer",
                        textAlign: "center",
                        transition: "all 0.2s",
                      }}
                    >
                      <div style={{ fontSize: 28, marginBottom: 4 }}>
                        {shape.emoji}
                      </div>
                      <Text style={{ fontSize: 11, color: "#666" }}>
                        {shape.name}
                      </Text>
                    </div>
                  ))}
                </div>
              </div>

              {/* OR Divider */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: 12,
                }}
              >
                <div style={{ flex: 1, height: 1, background: "#eee" }} />
                <Text
                  style={{ padding: "0 10px", color: "#bbb", fontSize: 11 }}
                >
                  OR
                </Text>
                <div style={{ flex: 1, height: 1, background: "#eee" }} />
              </div>
              </>
              )}

              {/* Mode Toggle */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: 8,
                  marginBottom: 8,
                }}
              >
                {[
                  { value: "type", icon: <FontSizeOutlined />, label: "Prompt" },
                  { value: "image", icon: <PictureOutlined />, label: "Upload" },
                  { value: "text", icon: <FontSizeOutlined />, label: "Text" },
                  // { value: "draw", icon: <EditOutlined />, label: "Draw" },  // Coming soon
                ].map((option) => (
                  <div
                    key={option.value}
                    onClick={() => setMode(option.value as InputMode)}
                    style={{
                      padding: "8px 4px",
                      borderRadius: 10,
                      border: mode === option.value ? `2px solid ${STRAVA_ORANGE}` : "2px solid #eee",
                      background: mode === option.value ? "#FFF5F0" : "#fafafa",
                      cursor: "pointer",
                      textAlign: "center",
                      transition: "all 0.2s",
                    }}
                  >
                    <div style={{ fontSize: 16, color: mode === option.value ? STRAVA_ORANGE : "#666", marginBottom: 2 }}>
                      {option.icon}
                    </div>
                    <Text strong style={{ fontSize: 12, display: "block", color: mode === option.value ? STRAVA_ORANGE : STRAVA_DARK }}>
                      {option.label}
                    </Text>
                  </div>
                ))}
              </div>

              {/* Mode Subtitle */}
              <Text style={{ fontSize: 12, color: "#888", display: "block", textAlign: "center", marginBottom: 12 }}>
                {mode === "type" && "✨ Describe your dream route shape"}
                {mode === "draw" && "🎨 Sketch it yourself (coming soon!)"}
                {mode === "text" && "🏃 Run your name or initials!"}
                {mode === "image" && "📸 Turn any image into a route"}
              </Text>

              {/* Prompt Input or Draw Placeholder */}
              {mode === "type" ? (
                <TextArea
                  value={prompt}
                  onChange={(e) => {
                    setPrompt(e.target.value);
                    setSelectedShape(null);
                  }}
                  placeholder="e.g., A route shaped like a dinosaur..."
                  autoSize={{ minRows: 2, maxRows: 3 }}
                  showCount
                  maxLength={200}
                  style={{ marginBottom: 12 }}
                />
              ) : mode === "text" ? (
                <Input
                  size="large"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value.toUpperCase())}
                  placeholder="e.g., NUS, 67, HI..."
                  maxLength={10}
                  style={{ marginBottom: 12, fontSize: 24, fontWeight: 700, textAlign: "center" }}
                />
              ) : mode === "image" ? (
                <div style={{ marginBottom: 12 }}>
                  <input
                    type="file"
                    accept="image/*"
                    id="image-upload"
                    style={{ display: "none" }}
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      
                      setIsUploadingImage(true);
                      try {
                        const result = await parseImage(file);
                        setImageSvgPath(result.svg_path);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Failed to parse image");
                      } finally {
                        setIsUploadingImage(false);
                      }
                    }}
                  />
                  <label htmlFor="image-upload">
                    <div
                      style={{
                        height: imageSvgPath ? 120 : 80,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        background: imageSvgPath ? "#f0fff0" : "#fafafa",
                        border: imageSvgPath ? `2px solid ${STRAVA_ORANGE}` : "1px dashed #d9d9d9",
                        borderRadius: 8,
                        cursor: isUploadingImage ? "wait" : "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      {isUploadingImage ? (
                        <>
                          <LoadingOutlined spin style={{ fontSize: 24, color: STRAVA_ORANGE }} />
                          <Text style={{ marginTop: 8, color: "#666" }}>Processing...</Text>
                        </>
                      ) : imageSvgPath ? (
                        <>
                          <svg width="60" height="60" viewBox="0 0 100 100" style={{ marginBottom: 4 }}>
                            <path d={imageSvgPath} fill="none" stroke={STRAVA_ORANGE} strokeWidth="2" />
                          </svg>
                          <Text style={{ color: "#52c41a", fontSize: 12 }}>✓ Shape detected! Click to change</Text>
                        </>
                      ) : (
                        <>
                          <UploadOutlined style={{ fontSize: 24, color: "#999" }} />
                          <Text style={{ marginTop: 8, color: "#666" }}>Click to upload an image</Text>
                          <Text style={{ fontSize: 11, color: "#999" }}>PNG, JPG, or SVG</Text>
                        </>
                      )}
                    </div>
                  </label>
                  {imageSvgPath && (
                    <Button 
                      type="link" 
                      size="small" 
                      onClick={() => setImageSvgPath(null)}
                      style={{ padding: 0, marginTop: 4 }}
                    >
                      Clear image
                    </Button>
                  )}
                </div>
              ) : (
                <div
                  style={{
                    height: 80,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "#fafafa",
                    border: "1px dashed #d9d9d9",
                    borderRadius: 8,
                    marginBottom: 20,
                  }}
                >
                  <Text type="secondary">Draw mode coming soon!</Text>
                </div>
              )}

              {/* Target Distance */}
              <div style={{ marginBottom: 20 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    marginBottom: 12,
                    gap: 8,
                  }}
                >
                  <Text strong style={{ color: STRAVA_DARK }}>
                    Target Distance:
                  </Text>
                  <Input
                    type="number"
                    step="0.1"
                    min={0}
                    max={sliderMax}
                    value={displayDistance.toFixed(1)}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      setDistanceFromDisplay(
                        Math.min(sliderMax, Math.max(0, val))
                      );
                    }}
                    style={{
                      width: 70,
                      fontWeight: 700,
                      color: STRAVA_ORANGE,
                      textAlign: "center",
                    }}
                  />
                  <Segmented
                    size="small"
                    value={unit}
                    onChange={(val) => setUnit(val as "km" | "mi")}
                    options={[
                      { label: "km", value: "km" },
                      { label: "mi", value: "mi" },
                    ]}
                  />
                </div>
                <Slider
                  min={0}
                  max={sliderMax}
                  step={0.5}
                  value={
                    unit === "km"
                      ? Math.min(distance, sliderMax)
                      : Math.min(distance * KM_TO_MI, sliderMax)
                  }
                  onChange={(val) =>
                    setDistance(unit === "km" ? val : val * MI_TO_KM)
                  }
                  marks={distanceMarks}
                  tooltip={{ formatter: (val) => `${val} ${unit}` }}
                  styles={{
                    track: { background: STRAVA_ORANGE },
                    rail: { background: "#eee" },
                  }}
                />
              </div>

              {/* Target Pace Removed */}

              {/* Error Alert */}
              {error && (
                <Alert
                  message="Generation Failed"
                  description={error}
                  type="error"
                  showIcon
                  closable
                  onClose={() => setError(null)}
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* CTA Button */}
              <Button
                block
                size="large"
                disabled={(mode === "type" && !prompt.trim()) || isGenerating}
                onClick={handleGenerate}
                loading={isGenerating}
                icon={!isGenerating ? <RocketOutlined /> : undefined}
                style={{
                  borderRadius: 8,
                  height: 48,
                  fontSize: 14,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: 1,
                  background:
                    ((mode === "type" && prompt.trim()) || (mode === "text" && textInput.trim()) || (mode === "image" && imageSvgPath) || mode === "draw") &&
                    !isGenerating
                      ? STRAVA_ORANGE
                      : "#f0f0f0",
                  color:
                    ((mode === "type" && prompt.trim()) || (mode === "text" && textInput.trim()) || (mode === "image" && imageSvgPath) || mode === "draw") &&
                    !isGenerating
                      ? "#fff"
                      : "#999",
                  border: "none",
                  boxShadow:
                    ((mode === "type" && prompt.trim()) || (mode === "text" && textInput.trim()) || (mode === "image" && imageSvgPath) || mode === "draw") &&
                    !isGenerating
                      ? `0 4px 12px ${STRAVA_ORANGE}40`
                      : "none",
                }}
              >
                {isGenerating
                  ? "Generating..."
                  : latitude
                  ? "Generate Route"
                  : "Get Location & Generate"}
              </Button>

              {/* Auto-Suggest Button */}
              <Button
                block
                size="large"
                disabled={isSuggesting || isGenerating}
                onClick={handleSuggest}
                loading={isSuggesting}
                style={{
                  marginTop: 12,
                  borderRadius: 8,
                  height: 44,
                  fontSize: 13,
                  fontWeight: 600,
                  background: isSuggesting ? "#f0f0f0" : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  color: isSuggesting ? "#999" : "#fff",
                  border: "none",
                  boxShadow: isSuggesting ? "none" : "0 4px 12px rgba(102, 126, 234, 0.4)",
                }}
              >
                {isSuggesting ? "Finding best shape..." : "✨ AI SUGGEST ROUTE"}
              </Button>
            </Card>
          </div>
        )}

        {/* Floating Error Alert for Route View (outside modal) */}
        {error && !showModal && generatedRoute && (
          <div
            style={{
              position: "absolute",
              top: 60,
              left: 16,
              right: 16,
              zIndex: 25,
              maxWidth: 400,
              margin: "0 auto",
            }}
          >
            <Alert
              message="Operation Failed"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{
                boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
                borderRadius: 8,
              }}
            />
          </div>
        )}

        {/* Slide-up Route Details Panel */}
        {generatedRoute && !showModal && (
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              zIndex: 15,
              background: "#fff",
              borderRadius: "20px 20px 0 0",
              boxShadow: "0 -4px 20px rgba(0,0,0,0.15)",
              animation: "slideUp 0.3s ease-out",
            }}
          >
            {/* Handle bar - Click to toggle minimize */}
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                padding: "12px 0 8px",
                cursor: "pointer",
              }}
              onClick={() => setIsMinimized(!isMinimized)}
            >
              <div
                style={{
                  width: 40,
                  height: 4,
                  background: "#ddd",
                  borderRadius: 2,
                }}
              />
            </div>

            <div
              style={{
                padding: "0 24px 24px",
                maxHeight: isMinimized ? 0 : 500,
                opacity: isMinimized ? 0 : 1,
                overflow: "hidden",
                transition: "all 0.3s ease-in-out",
              }}
            >
              {/* Title */}
              <Title level={4} style={{ marginBottom: 16, color: STRAVA_DARK }}>
                Your Route is Ready! 🎉
              </Title>

              {/* Stats Row */}
              <div
                style={{
                  display: "flex",
                  gap: 24,
                  marginBottom: 20,
                  flexWrap: "wrap",
                }}
              >
                <div>
                  <Text
                    style={{ fontSize: 11, color: "#888", display: "block" }}
                  >
                    Distance
                  </Text>
                  <Text strong style={{ fontSize: 18, color: STRAVA_DARK }}>
                    {routeStats
                      ? unit === "km"
                        ? `${(routeStats.distance_m / 1000).toFixed(1)} km`
                        : `${(
                            (routeStats.distance_m / 1000) *
                            KM_TO_MI
                          ).toFixed(1)} mi`
                      : "--"}
                  </Text>
                </div>
                <div>
                  <Text
                    style={{ fontSize: 11, color: "#888", display: "block" }}
                  >
                    Shape
                  </Text>
                  <Text strong style={{ fontSize: 18, color: STRAVA_DARK }}>
                    {inputPrompt || prompt || selectedShape || "Custom Shape"}
                  </Text>
                </div>
              </div>

              {/* Overlay Toggle */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 16,
                  padding: "8px 12px",
                  background: "#f5f5f5",
                  borderRadius: 8,
                  cursor: "pointer",
                }}
                onClick={() => setShowOverlay(!showOverlay)}
              >
                <input
                  type="checkbox"
                  checked={showOverlay}
                  onChange={() => setShowOverlay(!showOverlay)}
                  style={{ width: 16, height: 16, cursor: "pointer" }}
                />
                <Text style={{ fontSize: 13, color: "#333" }}>
                  Show resize handles
                </Text>
              </div>

              {/* Action Buttons - Horizontal */}
              <div style={{ display: "flex", gap: 12 }}>
                <Button
                  size="large"
                  type="primary"
                  icon={<DownloadOutlined />}
                  loading={isExporting}
                  style={{
                    flex: 1,
                    background: STRAVA_ORANGE,
                    borderColor: STRAVA_ORANGE,
                    borderRadius: 10,
                    height: 48,
                    fontWeight: 600,
                  }}
                  onClick={async () => {
                    if (!latitude || !longitude) return;
                    setIsExporting(true);
                    try {
                      await exportGPX({
                        start_lat: latitude,
                        start_lng: longitude,
                        distance_km: distance,
                        aspect_ratio: aspectRatio,
                        ...(mode === "type" && prompt.trim()
                          ? { prompt: prompt.trim() }
                          : { shape_id: selectedShape || "heart" }),
                      });
                    } catch (err) {
                      console.error("Export failed:", err);
                      setError(
                        err instanceof Error
                          ? err.message
                          : "Failed to export GPX file."
                      );
                    } finally {
                      setIsExporting(false);
                    }
                  }}
                >
                  {isExporting ? "Exporting..." : "Export GPX"}
                </Button>
                <Button
                  size="large"
                  style={{ flex: 1, borderRadius: 10, height: 48 }}
                  onClick={() => {
                    setShowModal(true);
                    setGeneratedRoute(null);
                    setGeneratedSvg(null);
                    setInputPrompt(null);
                  }}
                >
                  Create New Route
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* CSS Animation */}
        <style jsx global>{`
          @keyframes slideUp {
            from {
              transform: translateY(100%);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
        `}</style>
      </main>
    </ConfigProvider>
  );
}
