"use client";

import MapComponent from "@/components/Map";
import { useState } from "react";
import { useLocation } from "@/hooks/use-location";
import { 
  Card, 
  Typography, 
  Segmented, 
  Input, 
  Button, 
  Space, 
  Alert,
  ConfigProvider,
  theme
} from "antd";
import { 
  EnvironmentOutlined, 
  EditOutlined, 
  FontSizeOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  RocketOutlined
} from "@ant-design/icons";

const { Title, Text } = Typography;
const { TextArea } = Input;

type InputMode = "draw" | "type";

export default function Home() {
  const [mode, setMode] = useState<InputMode>("type");
  const [prompt, setPrompt] = useState("");
  const { latitude, error, loading: locationLoading, getCurrentLocation } = useLocation();

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 8,
        },
      }}
    >
      <main className="relative w-full h-full min-h-screen">
        <MapComponent />

        {/* Overlay UI Container */}
        <div
          style={{
            position: "absolute",
            top: 16,
            left: 16,
            zIndex: 10,
            maxWidth: 380,
            pointerEvents: "none",
          }}
        >
          <Card
            style={{
              pointerEvents: "auto",
              backdropFilter: "blur(12px)",
              background: "rgba(255, 255, 255, 0.95)",
            }}
            styles={{ body: { padding: 20 } }}
          >
            <Title
              level={4}
              style={{
                marginBottom: 4,
                background: "linear-gradient(90deg, #1677ff, #722ed1)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              PathArt
            </Title>
            <Text type="secondary" style={{ fontSize: 11, letterSpacing: 1 }}>
              AI-POWERED ROUTE DESIGNER
            </Text>

            {/* Mode Toggles */}
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
              style={{ marginTop: 16, marginBottom: 16 }}
            />

            {/* Input Area */}
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              {mode === "type" ? (
                <TextArea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., A running route shaped like a dinosaur..."
                  autoSize={{ minRows: 3, maxRows: 4 }}
                  showCount
                  maxLength={200}
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
                  }}
                >
                  <Text type="secondary">Draw mode coming soon!</Text>
                </div>
              )}

              {/* Location Picker */}
              <Button
                block
                icon={
                  locationLoading ? (
                    <LoadingOutlined spin />
                  ) : latitude ? (
                    <CheckCircleOutlined style={{ color: "#52c41a" }} />
                  ) : (
                    <EnvironmentOutlined />
                  )
                }
                onClick={getCurrentLocation}
                loading={locationLoading}
                type={latitude ? "default" : "dashed"}
                style={latitude ? { borderColor: "#b7eb8f", background: "#f6ffed" } : {}}
              >
                {latitude ? "Location Acquired" : "Use Current Location"}
              </Button>

              {error && <Alert message={error} type="error" showIcon />}

              {/* Generate Button */}
              <Button
                type="primary"
                block
                size="large"
                icon={<RocketOutlined />}
              >
                Generate Route
              </Button>
            </Space>
          </Card>
        </div>
      </main>
    </ConfigProvider>
  );
}
