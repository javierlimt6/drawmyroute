"use client";

import MapComponent from "@/components/Map";
import { useState } from "react";
import { useLocation } from "@/hooks/use-location";
import {
  Card,
  Typography,
  Input,
  Button,
  Space,
  ConfigProvider,
  Segmented,
  Slider,
} from "antd";
import {
  EnvironmentOutlined,
  SearchOutlined,
  LoadingOutlined,
  AimOutlined,
  EditOutlined,
  FontSizeOutlined,
  RocketOutlined,
} from "@ant-design/icons";

const { Title, Text } = Typography;
const { TextArea } = Input;

// Strava brand colors
const STRAVA_ORANGE = "#FC4C02";
const STRAVA_DARK = "#1A1A1A";

type InputMode = "type" | "draw";

interface PredefinedShape {
  id: string;
  name: string;
  emoji: string;
  prompt: string;
}

const PREDEFINED_SHAPES: PredefinedShape[] = [
  { id: "heart", name: "Heart", emoji: "❤️", prompt: "A route shaped like a heart" },
  { id: "star", name: "Star", emoji: "⭐", prompt: "A route shaped like a 5-point star" },
  { id: "circle", name: "Circle", emoji: "⭕", prompt: "A circular loop route" },
  { id: "figure8", name: "Figure 8", emoji: "♾️", prompt: "A route shaped like a figure 8" },
  { id: "lightning", name: "Lightning", emoji: "⚡", prompt: "A route shaped like a lightning bolt" },
  { id: "dinosaur", name: "Dinosaur", emoji: "🦖", prompt: "A route shaped like a T-Rex dinosaur" },
  { id: "singapore", name: "SG", emoji: "🇸🇬", prompt: "A route shaped like Singapore's outline" },
  { id: "merlion", name: "Merlion", emoji: "🦁", prompt: "A route shaped like the Merlion" },
];

export default function Home() {
  const [showModal, setShowModal] = useState(true);
  const [mode, setMode] = useState<InputMode>("type");
  const [prompt, setPrompt] = useState("");
  const [selectedShape, setSelectedShape] = useState<string | null>(null);
  const [distance, setDistance] = useState(5); // Always stored in km
  const [unit, setUnit] = useState<"km" | "mi">("km");
  const [searchValue, setSearchValue] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRoute, setGeneratedRoute] = useState<GeoJSON.LineString | null>(null);
  const { latitude, longitude, loading: locationLoading, getCurrentLocation } = useLocation();

  // Conversion helpers
  const KM_TO_MI = 0.621371;
  const MI_TO_KM = 1.60934;
  
  const displayDistance = unit === "km" ? distance : distance * KM_TO_MI;
  const setDistanceFromDisplay = (val: number) => {
    setDistance(unit === "km" ? val : val * MI_TO_KM);
  };

  // Mock route generation (replace with real API later)
  const handleGenerate = async () => {
    if (!latitude || !longitude) {
      getCurrentLocation();
      return;
    }
    
    setIsGenerating(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock heart-shaped route centered on user location
    const mockRoute: GeoJSON.LineString = {
      type: "LineString",
      coordinates: [
        [longitude, latitude],
        [longitude + 0.008, latitude + 0.012],
        [longitude + 0.016, latitude + 0.008],
        [longitude + 0.012, latitude],
        [longitude + 0.016, latitude - 0.008],
        [longitude + 0.008, latitude - 0.012],
        [longitude, latitude],
        [longitude - 0.008, latitude - 0.012],
        [longitude - 0.016, latitude - 0.008],
        [longitude - 0.012, latitude],
        [longitude - 0.016, latitude + 0.008],
        [longitude - 0.008, latitude + 0.012],
        [longitude, latitude],
      ]
    };
    
    setGeneratedRoute(mockRoute);
    setIsGenerating(false);
    setShowModal(false);
  };

  const distanceMarks = unit === "km" 
    ? { 1: "1", 5: "5", 10: "10", 15: "15", 20: "20" }
    : { 1: "0.6", 5: "3", 10: "6", 15: "9", 20: "12" };

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: STRAVA_ORANGE,
          borderRadius: 8,
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
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
          {/* Subtitle */}
          <div
            style={{
              background: "#111",
              padding: "6px 0",
              textAlign: "center",
              borderBottom: "1px solid #333",
            }}
          >
            <Text style={{ color: "#888", fontSize: 11 }}>
              A Hack&Roll 2026 product by <span style={{ color: STRAVA_ORANGE }}>duo showdown</span>
            </Text>
          </div>
          
          {/* Main Header */}
          <div
            style={{
              padding: "10px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            {/* Left spacer */}
            <div style={{ width: 80 }} />
            
            {/* Center logo */}
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill={STRAVA_ORANGE}>
                <path d="M12 2L4 20h5l3-6 3 6h5L12 2zm0 10l-1.5 3h3L12 12z" />
              </svg>
              <Text strong style={{ color: "#fff", fontSize: 18, letterSpacing: 1 }}>
                DrawMyRoute
              </Text>
            </div>
            
            {/* GitHub link */}
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
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              GitHub
            </a>
          </div>
        </div>

        {/* Map with overlay */}
        <div style={{ position: "relative", width: "100%", height: "100%" }}>
          <MapComponent 
            route={generatedRoute} 
            center={longitude && latitude ? [longitude, latitude] : undefined}
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
                <Title level={4} style={{ margin: 0, fontWeight: 700, color: STRAVA_DARK }}>
                  🗺️ DrawMyRoute
                </Title>
                <Text style={{ fontSize: 12, color: "#888" }}>
                  Create custom routes shaped to your imagination
                </Text>
              </div>

              {/* Location Search */}
              <Input
                size="large"
                placeholder="Enter starting location..."
                prefix={<SearchOutlined style={{ color: "#999" }} />}
                suffix={
                  <Button
                    type="text"
                    size="small"
                    icon={locationLoading ? <LoadingOutlined spin /> : <AimOutlined />}
                    onClick={getCurrentLocation}
                    style={{ color: latitude ? "#52c41a" : STRAVA_ORANGE }}
                  />
                }
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                style={{ marginBottom: 20, borderRadius: 8, height: 48 }}
              />

              {/* Predefined Shapes Selector */}
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: "block", marginBottom: 10, color: STRAVA_DARK }}>
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
                        }
                      }}
                      style={{
                        minWidth: 72,
                        padding: "12px 8px",
                        borderRadius: 12,
                        border: selectedShape === shape.id 
                          ? `2px solid ${STRAVA_ORANGE}` 
                          : "2px solid #eee",
                        background: selectedShape === shape.id ? "#FFF5F0" : "#fff",
                        cursor: "pointer",
                        textAlign: "center",
                        transition: "all 0.2s",
                      }}
                    >
                      <div style={{ fontSize: 28, marginBottom: 4 }}>{shape.emoji}</div>
                      <Text style={{ fontSize: 11, color: "#666" }}>{shape.name}</Text>
                    </div>
                  ))}
                </div>
              </div>

              {/* OR Divider */}
              <div style={{ display: "flex", alignItems: "center", marginBottom: 12 }}>
                <div style={{ flex: 1, height: 1, background: "#eee" }} />
                <Text style={{ padding: "0 10px", color: "#bbb", fontSize: 11 }}>OR</Text>
                <div style={{ flex: 1, height: 1, background: "#eee" }} />
              </div>

              {/* Mode Toggle */}
              <Segmented
                block
                value={mode}
                onChange={(val) => setMode(val as InputMode)}
                options={[
                  {
                    label: (
                      <Space>
                        <FontSizeOutlined />
                        Type Prompt
                      </Space>
                    ),
                    value: "type",
                  },
                  {
                    label: (
                      <Space>
                        <EditOutlined />
                        Draw Shape
                      </Space>
                    ),
                    value: "draw",
                  },
                ]}
                style={{ marginBottom: 16 }}
              />

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
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", alignItems: "center", marginBottom: 12, gap: 8 }}>
                  <Text strong style={{ color: STRAVA_DARK }}>
                    Target Distance:
                  </Text>
                  <Input
                    type="number"
                    step="0.1"
                    min={0.5}
                    max={100}
                    value={displayDistance.toFixed(1)}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0.5;
                      setDistanceFromDisplay(Math.min(100, Math.max(0.5, val)));
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
                  min={1}
                  max={20}
                  step={0.5}
                  value={Math.min(distance, 20)}
                  onChange={setDistance}
                  marks={distanceMarks}
                  tooltip={{ formatter: (val) => `${unit === "km" ? val : (val! * KM_TO_MI).toFixed(1)} ${unit}` }}
                  styles={{
                    track: { background: STRAVA_ORANGE },
                    rail: { background: "#eee" },
                  }}
                />
                {distance > 20 && (
                  <Text style={{ fontSize: 11, color: "#999", marginTop: 4, display: "block" }}>
                    Custom: {displayDistance.toFixed(1)} {unit} (slider max is {unit === "km" ? "20 km" : "12.4 mi"})
                  </Text>
                )}
              </div>

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
                  background: ((mode === "type" && prompt.trim()) || mode === "draw") && !isGenerating ? STRAVA_ORANGE : "#f0f0f0",
                  color: ((mode === "type" && prompt.trim()) || mode === "draw") && !isGenerating ? "#fff" : "#999",
                  border: "none",
                  boxShadow: ((mode === "type" && prompt.trim()) || mode === "draw") && !isGenerating ? `0 4px 12px ${STRAVA_ORANGE}40` : "none",
                }}
              >
                {isGenerating ? "Generating..." : latitude ? "Generate Route" : "Get Location & Generate"}
              </Button>
            </Card>
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
            {/* Handle bar */}
            <div style={{ display: "flex", justifyContent: "center", padding: "12px 0 8px" }}>
              <div style={{ width: 40, height: 4, background: "#ddd", borderRadius: 2 }} />
            </div>

            <div style={{ padding: "0 24px 24px" }}>
              {/* Title */}
              <Title level={4} style={{ marginBottom: 16, color: STRAVA_DARK }}>
                Your Route is Ready! 🎉
              </Title>

              {/* Stats Row */}
              <div style={{ display: "flex", gap: 24, marginBottom: 20 }}>
                <div>
                  <Text style={{ fontSize: 11, color: "#888", display: "block" }}>Distance</Text>
                  <Text strong style={{ fontSize: 18, color: STRAVA_DARK }}>
                    {unit === "km" ? `${distance.toFixed(1)} km` : `${(distance * KM_TO_MI).toFixed(1)} mi`}
                  </Text>
                </div>
                <div>
                  <Text style={{ fontSize: 11, color: "#888", display: "block" }}>Est. Time</Text>
                  <Text strong style={{ fontSize: 18, color: STRAVA_DARK }}>
                    {Math.round(distance * 6)} min
                  </Text>
                </div>
                <div>
                  <Text style={{ fontSize: 11, color: "#888", display: "block" }}>Pace</Text>
                  <Text strong style={{ fontSize: 18, color: STRAVA_DARK }}>
                    6:00 /km
                  </Text>
                </div>
              </div>

              {/* Motivational Quote */}
              <div
                style={{
                  background: `linear-gradient(90deg, ${STRAVA_ORANGE}15, #FFD70015, #90EE9015)`,
                  padding: "14px 18px",
                  borderRadius: 12,
                  marginBottom: 20,
                  borderLeft: `3px solid ${STRAVA_ORANGE}`,
                }}
              >
                <Text italic style={{ color: "#555", fontSize: 14 }}>
                  "Sometimes the best journeys are the ones with no destination."
                </Text>
              </div>

              {/* Action Buttons */}
              <Space style={{ width: "100%" }} direction="vertical" size="small">
                <Button
                  block
                  size="large"
                  type="primary"
                  icon={<RocketOutlined />}
                  style={{
                    background: STRAVA_ORANGE,
                    borderColor: STRAVA_ORANGE,
                    borderRadius: 10,
                    height: 48,
                    fontWeight: 600,
                  }}
                  onClick={() => {
                    // TODO: Open in Strava or start navigation
                    window.open(`https://www.google.com/maps/dir/?api=1&origin=${latitude},${longitude}&destination=${latitude},${longitude}&travelmode=walking`, '_blank');
                  }}
                >
                  Start Route
                </Button>
                <Button
                  block
                  size="large"
                  style={{ borderRadius: 10, height: 44 }}
                  onClick={() => {
                    setShowModal(true);
                    setGeneratedRoute(null);
                  }}
                >
                  Generate New Route
                </Button>
              </Space>
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
