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

export default function Home() {
  const [showModal, setShowModal] = useState(true);
  const [mode, setMode] = useState<InputMode>("type");
  const [prompt, setPrompt] = useState("");
  const [distance, setDistance] = useState(5); // km
  const [searchValue, setSearchValue] = useState("");
  const { latitude, loading: locationLoading, getCurrentLocation } = useLocation();

  const handleGenerate = () => {
    if (!latitude) {
      getCurrentLocation();
      return;
    }
    setShowModal(false);
    // TODO: Call backend API with prompt, distance, lat/lng
  };

  const distanceMarks = {
    1: "1km",
    5: "5km",
    10: "10km",
    15: "15km",
    20: "20km",
  };

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
          <MapComponent />
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
                maxWidth: 440,
                borderRadius: 12,
                boxShadow: "0 12px 40px rgba(0,0,0,0.3)",
                border: "none",
              }}
              styles={{ body: { padding: 32 } }}
            >
              {/* Icon */}
              <div style={{ textAlign: "center", marginBottom: 20 }}>
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    background: `linear-gradient(135deg, ${STRAVA_ORANGE}, #FF6B35)`,
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="#fff">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                  </svg>
                </div>
              </div>

              {/* Title */}
              <Title
                level={2}
                style={{
                  textAlign: "center",
                  marginBottom: 8,
                  fontWeight: 700,
                  color: STRAVA_DARK,
                }}
              >
                Draw Your Route
              </Title>
              <Text
                style={{
                  display: "block",
                  textAlign: "center",
                  color: "#666",
                  marginBottom: 24,
                }}
              >
                Create custom routes shaped to your imagination
              </Text>

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
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., A route shaped like a dinosaur, a heart, a star..."
                  autoSize={{ minRows: 3, maxRows: 4 }}
                  showCount
                  maxLength={200}
                  style={{ marginBottom: 20 }}
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
                <Text strong style={{ display: "block", marginBottom: 12, color: STRAVA_DARK }}>
                  Target Distance: <span style={{ color: STRAVA_ORANGE }}>{distance} km</span>
                </Text>
                <Slider
                  min={1}
                  max={20}
                  value={distance}
                  onChange={setDistance}
                  marks={distanceMarks}
                  tooltip={{ formatter: (val) => `${val} km` }}
                  styles={{
                    track: { background: STRAVA_ORANGE },
                    rail: { background: "#eee" },
                  }}
                />
              </div>

              {/* CTA Button */}
              <Button
                block
                size="large"
                disabled={mode === "type" && !prompt.trim()}
                onClick={handleGenerate}
                icon={<RocketOutlined />}
                style={{
                  borderRadius: 8,
                  height: 52,
                  fontSize: 16,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: 1,
                  background: (mode === "type" && prompt.trim()) || mode === "draw" ? STRAVA_ORANGE : "#f0f0f0",
                  color: (mode === "type" && prompt.trim()) || mode === "draw" ? "#fff" : "#999",
                  border: "none",
                  boxShadow: (mode === "type" && prompt.trim()) || mode === "draw" ? `0 4px 12px ${STRAVA_ORANGE}40` : "none",
                }}
              >
                {latitude ? "Generate Route" : "Get Location & Generate"}
              </Button>
            </Card>
          </div>
        )}
      </main>
    </ConfigProvider>
  );
}
