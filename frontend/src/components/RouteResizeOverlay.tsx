"use client";

import React, { useState, useCallback, useEffect } from "react";

const OVERLAY_BLACK = "#1a1a1a";
const MOVE_DARK = "#333333";

interface RouteResizeOverlayProps {
  bounds: {
    minLng: number;
    maxLng: number;
    minLat: number;
    maxLat: number;
  } | null;
  mapRef: mapboxgl.Map | null;
  onResize: (ratio: number, dimension: "width" | "height") => void;
  onMove?: (newLat: number, newLng: number) => void;
  disabled?: boolean;
  svgPath?: string | null;
}

export default function RouteResizeOverlay({
  bounds,
  mapRef,
  onResize,
  onMove,
  disabled = false,
  svgPath,
}: RouteResizeOverlayProps) {
  const [screenBounds, setScreenBounds] = useState<{
    left: number;
    top: number;
    width: number;
    height: number;
  } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragEdge, setDragEdge] = useState<string | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [initialBounds, setInitialBounds] = useState<{
    left: number;
    top: number;
    width: number;
    height: number;
  } | null>(null);

  // Convert GPS bounds to screen coordinates
  const updateScreenBounds = useCallback(() => {
    if (!bounds || !mapRef) return;

    const topLeft = mapRef.project([bounds.minLng, bounds.maxLat]);
    const bottomRight = mapRef.project([bounds.maxLng, bounds.minLat]);

    setScreenBounds({
      left: topLeft.x,
      top: topLeft.y,
      width: bottomRight.x - topLeft.x,
      height: bottomRight.y - topLeft.y,
    });
  }, [bounds, mapRef]);

  // Update on bounds change and map movement (but NOT while dragging)
  useEffect(() => {
    if (!isDragging) {
      updateScreenBounds();
    }

    if (mapRef) {
      const handleMapMove = () => {
        if (!isDragging) {
          updateScreenBounds();
        }
      };
      mapRef.on("move", handleMapMove);
      mapRef.on("zoom", handleMapMove);
      return () => {
        mapRef.off("move", handleMapMove);
        mapRef.off("zoom", handleMapMove);
      };
    }
  }, [mapRef, updateScreenBounds, isDragging]);

  // Handle drag start (edge or center)
  const handleMouseDown = (e: React.MouseEvent, edge: string) => {
    if (disabled) return;
    e.preventDefault();
    e.stopPropagation();
    
    setIsDragging(true);
    setDragEdge(edge);
    setDragStart({ x: e.clientX, y: e.clientY });
    if (screenBounds) {
      setInitialBounds({ ...screenBounds });
    }
  };

  // Handle drag move
  useEffect(() => {
    if (!isDragging || !dragStart || !initialBounds || !dragEdge) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;
      
      let newWidth = initialBounds.width;
      let newHeight = initialBounds.height;
      let newLeft = initialBounds.left;
      let newTop = initialBounds.top;

      if (dragEdge === "center") {
        // Move the entire box
        newLeft = initialBounds.left + deltaX;
        newTop = initialBounds.top + deltaY;
      } else if (dragEdge === "top") {
        newHeight = Math.max(50, initialBounds.height - deltaY);
        newTop = initialBounds.top + deltaY;
        const scaleFactor = newHeight / initialBounds.height;
        newWidth = initialBounds.width / scaleFactor;
        newLeft = initialBounds.left + (initialBounds.width - newWidth) / 2;
      } else if (dragEdge === "bottom") {
        newHeight = Math.max(50, initialBounds.height + deltaY);
        const scaleFactor = newHeight / initialBounds.height;
        newWidth = initialBounds.width / scaleFactor;
        newLeft = initialBounds.left + (initialBounds.width - newWidth) / 2;
      } else if (dragEdge === "left") {
        newWidth = Math.max(50, initialBounds.width - deltaX);
        newLeft = initialBounds.left + deltaX;
        const scaleFactor = newWidth / initialBounds.width;
        newHeight = initialBounds.height / scaleFactor;
        newTop = initialBounds.top + (initialBounds.height - newHeight) / 2;
      } else if (dragEdge === "right") {
        newWidth = Math.max(50, initialBounds.width + deltaX);
        const scaleFactor = newWidth / initialBounds.width;
        newHeight = initialBounds.height / scaleFactor;
        newTop = initialBounds.top + (initialBounds.height - newHeight) / 2;
      }

      setScreenBounds({
        left: newLeft,
        top: newTop,
        width: newWidth,
        height: newHeight,
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      
      if (screenBounds && initialBounds && mapRef) {
        if (dragEdge === "center" && onMove) {
          // Calculate new center GPS coordinates
          const centerX = screenBounds.left + screenBounds.width / 2;
          const centerY = screenBounds.top + screenBounds.height / 2;
          const newCenter = mapRef.unproject([centerX, centerY]);
          onMove(newCenter.lat, newCenter.lng);
        } else {
          // Differentiate between width and height drags
          if (dragEdge === "left" || dragEdge === "right") {
            // Width drag: send width ratio for adaptive resize
            const widthRatio = screenBounds.width / initialBounds.width;
            onResize(widthRatio, "width");
          } else {
            // Height drag: send aspect ratio change
            const originalAspect = initialBounds.height / initialBounds.width;
            const newAspect = screenBounds.height / screenBounds.width;
            const aspectRatioChange = newAspect / originalAspect;
            onResize(aspectRatioChange, "height");
          }
        }
      }
      
      setDragStart(null);
      setDragEdge(null);
      setInitialBounds(null);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, dragStart, dragEdge, initialBounds, screenBounds, onResize, onMove, mapRef]);

  if (!screenBounds || !bounds) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: screenBounds.left,
        top: screenBounds.top,
        width: screenBounds.width,
        height: screenBounds.height,
        pointerEvents: "none",
        zIndex: 10,
      }}
    >
      {/* Dashed bounding box */}
      <svg
        width="100%"
        height="100%"
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <rect
          x={1}
          y={1}
          width={screenBounds.width - 2}
          height={screenBounds.height - 2}
          fill="none"
          stroke={OVERLAY_BLACK}
          strokeWidth={2}
          strokeDasharray="6 4"
          opacity={0.8}
        />
      </svg>

      {/* SVG Shape Overlay */}
      {svgPath && (
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          width="100%"
          height="100%"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            opacity: 0.4,
            pointerEvents: "none",
          }}
        >
          <path
            d={svgPath}
            fill="none"
            stroke="#FC4C02"
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      )}

      {/* Interior draggable area for moving (excludes edge handle zones) */}
      {onMove && (
        <div
          onMouseDown={(e) => handleMouseDown(e, "center")}
          style={{
            position: "absolute",
            left: 20,
            top: 20,
            width: Math.max(0, screenBounds.width - 40),
            height: Math.max(0, screenBounds.height - 40),
            background: "transparent",
            cursor: disabled ? "not-allowed" : "move",
            pointerEvents: "auto",
          }}
        />
      )}

      {/* Top edge handle */}
      <div
        onMouseDown={(e) => handleMouseDown(e, "top")}
        style={{
          position: "absolute",
          left: screenBounds.width / 2 - 16,
          top: -6,
          width: 32,
          height: 12,
          background: "#fff",
          border: `2px solid ${OVERLAY_BLACK}`,
          borderRadius: 6,
          cursor: disabled ? "not-allowed" : "ns-resize",
          pointerEvents: "auto",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }}
      />
      {/* Bottom edge handle */}
      <div
        onMouseDown={(e) => handleMouseDown(e, "bottom")}
        style={{
          position: "absolute",
          left: screenBounds.width / 2 - 16,
          top: screenBounds.height - 6,
          width: 32,
          height: 12,
          background: "#fff",
          border: `2px solid ${OVERLAY_BLACK}`,
          borderRadius: 6,
          cursor: disabled ? "not-allowed" : "ns-resize",
          pointerEvents: "auto",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }}
      />
      {/* Left edge handle */}
      <div
        onMouseDown={(e) => handleMouseDown(e, "left")}
        style={{
          position: "absolute",
          left: -6,
          top: screenBounds.height / 2 - 16,
          width: 12,
          height: 32,
          background: "#fff",
          border: `2px solid ${OVERLAY_BLACK}`,
          borderRadius: 6,
          cursor: disabled ? "not-allowed" : "ew-resize",
          pointerEvents: "auto",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }}
      />
      {/* Right edge handle */}
      <div
        onMouseDown={(e) => handleMouseDown(e, "right")}
        style={{
          position: "absolute",
          left: screenBounds.width - 6,
          top: screenBounds.height / 2 - 16,
          width: 12,
          height: 32,
          background: "#fff",
          border: `2px solid ${OVERLAY_BLACK}`,
          borderRadius: 6,
          cursor: disabled ? "not-allowed" : "ew-resize",
          pointerEvents: "auto",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }}
      />

      {/* Drag label */}
      {isDragging && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            background: "rgba(0,0,0,0.7)",
            color: "#fff",
            padding: "4px 8px",
            borderRadius: 4,
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {dragEdge === "center" ? "Moving..." : "Resizing..."}
        </div>
      )}
    </div>
  );
}
