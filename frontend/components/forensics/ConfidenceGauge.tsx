"use client";
import React from "react";

interface ConfidenceGaugeProps {
  score: number;
  isTampered: boolean;
  size?: number;
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({
  score,
  isTampered,
  size = 120,
}) => {
  const radius = size * 0.4;
  const stroke = size * 0.08;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - score * circumference;

  const color = isTampered ? "var(--accent-danger)" : "var(--accent-success)";

  return (
    <div className="confidence-gauge" style={{ width: size, height: size, position: "relative" }}>
      <svg height={size} width={size}>
        <circle
          stroke="var(--border)"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={size / 2}
          cy={size / 2}
        />
        <circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={circumference + " " + circumference}
          style={{ strokeDashoffset, transition: "stroke-dashoffset 0.8s ease-in-out", transform: "rotate(-90deg)", transformOrigin: "50% 50%" }}
          r={normalizedRadius}
          cx={size / 2}
          cy={size / 2}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: size,
          height: size,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: size * 0.18, fontWeight: 800, color: "var(--text-primary)" }}>
          {(score * 100).toFixed(0)}%
        </span>
        <span style={{ fontSize: size * 0.08, color: "var(--text-secondary)", fontWeight: 500, textTransform: "uppercase" }}>
          Confidence
        </span>
      </div>
    </div>
  );
};
