"use client";
import React from "react";

interface ElaHeatmapProps {
    id: string;
    filename?: string;
}

export const ElaHeatmap: React.FC<ElaHeatmapProps> = ({ id, filename }) => {
    return (
        <div className="ela-container">
            <div className="ela-header" style={{ marginBottom: "0.75rem" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    Error Level Analysis (ELA)
                </h3>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    Highlights pixel differences after fixed-rate JPEG re-compression.
                </p>
            </div>

            <div className="ela-frame" style={{
                position: "relative",
                borderRadius: "var(--radius-md)",
                overflow: "hidden",
                border: "1px solid var(--border)",
                background: "#000"
            }}>
                <img
                    src={`/api/v1/analysis/${id}/heatmap`}
                    alt={`ELA Heatmap for ${filename || 'evidence'}`}
                    style={{
                        width: "100%",
                        display: "block",
                        filter: "contrast(1.2) brightness(1.1)"
                    }}
                    onError={(e) => {
                        (e.target as HTMLImageElement).parentElement!.style.display = "none";
                    }}
                />

                <div style={{
                    position: "absolute",
                    bottom: "10px",
                    right: "10px",
                    background: "rgba(0,0,0,0.6)",
                    backdropFilter: "blur(4px)",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "0.7rem",
                    color: "#fff",
                    border: "1px solid rgba(255,255,255,0.1)"
                }}>
                    Forensic Heatmap
                </div>
            </div>

            <div style={{ marginTop: "0.75rem", display: "flex", gap: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: "#fff" }}></div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Modified Area</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: "#222" }}></div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Authentic Area</span>
                </div>
            </div>
        </div>
    );
};
