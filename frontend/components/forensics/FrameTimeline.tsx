"use client";
import React from "react";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";

interface FrameResult {
    frame_no: number;
    is_tampered: boolean;
    confidence: number;
}

interface FrameTimelineProps {
    data: FrameResult[];
}

export const FrameTimeline: React.FC<FrameTimelineProps> = ({ data }) => {
    return (
        <div className="timeline-container">
            <div className="timeline-header" style={{ marginBottom: "1rem" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    Temporal Tampering Timeline
                </h3>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    Per-frame analysis identifying inconsistencies across the video duration.
                </p>
            </div>

            <div style={{ height: 240, width: "100%", background: "var(--bg-surface)", padding: "1rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 5, right: 10, bottom: 20, left: 0 }}>
                        <XAxis
                            dataKey="frame_no"
                            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                            label={{ value: "Frame Index", position: "insideBottom", offset: -5, fill: "var(--text-muted)", fontSize: 10 }}
                        />
                        <YAxis
                            domain={[0, 1]}
                            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                        />
                        <Tooltip
                            contentStyle={{
                                background: "var(--bg-card)",
                                border: "1px solid var(--border)",
                                borderRadius: 8,
                                fontSize: "0.85rem"
                            }}
                            formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Confidence"]}
                            labelFormatter={(label: number) => `Frame #${label}`}
                        />
                        <ReferenceLine
                            y={0.5}
                            stroke="var(--accent-warn)"
                            strokeDasharray="4 3"
                            label={{ value: "Limit", fill: "var(--accent-warn)", fontSize: 9, position: "insideTopRight" }}
                        />
                        <Bar dataKey="confidence" radius={[2, 2, 0, 0]}>
                            {data.map((f: FrameResult, i: number) => (
                                <Cell
                                    key={i}
                                    fill={f.is_tampered ? "var(--accent-danger)" : "var(--accent-success)"}
                                    fillOpacity={0.8}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div style={{ marginTop: "0.75rem", display: "flex", gap: "1rem", justifyContent: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent-danger)" }}></div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Tampered Frame</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent-success)" }}></div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Authentic Frame</span>
                </div>
            </div>
        </div>
    );
};
