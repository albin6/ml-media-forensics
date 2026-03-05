"use client";
import React, { useState, useEffect } from "react";
import { adminApi } from "@/lib/api";
import {
    Shield, History, Users, Settings,
    Activity, Database, CheckCircle, AlertTriangle
} from "lucide-react";

interface AuditLog {
    id: string;
    user_id: string | null;
    event_type: string;
    resource_id: string | null;
    ip_address: string | null;
    details: any;
    occurred_at: string;
}

interface ModelVersion {
    id: string;
    model_name: string;
    version_tag: string;
    architecture: string;
    f1_score: number | null;
    is_active: boolean;
    registered_at: string;
}

export default function AdminDashboard() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [models, setModels] = useState<ModelVersion[]>([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<"logs" | "models">("logs");

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [logsRes, modelsRes] = await Promise.all([
                adminApi.auditLogs(),
                adminApi.models()
            ]);
            setLogs(logsRes.data);
            setModels(modelsRes.data);
        } catch (err) {
            console.error("Failed to load admin data", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="page-container" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
                <Activity className="pulsing" color="var(--accent-primary)" size={32} />
            </div>
        );
    }

    return (
        <div className="page-container animate-in">
            <header style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
                    <Shield size={28} color="var(--accent-primary)" />
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Forensic Administration</h1>
                </div>
                <p style={{ color: "var(--text-secondary)" }}>
                    Monitor system integrity, chain of custody, and model performance metrics.
                </p>
            </header>

            {/* ── Tabs ── */}
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", borderBottom: "1px solid var(--border)" }}>
                <button
                    onClick={() => setTab("logs")}
                    style={{
                        padding: "0.75rem 1rem",
                        background: "transparent",
                        border: "none",
                        borderBottom: tab === "logs" ? "2px solid var(--accent-primary)" : "2px solid transparent",
                        color: tab === "logs" ? "var(--text-primary)" : "var(--text-muted)",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem"
                    }}
                >
                    <History size={16} /> Audit Trail
                </button>
                <button
                    onClick={() => setTab("models")}
                    style={{
                        padding: "0.75rem 1rem",
                        background: "transparent",
                        border: "none",
                        borderBottom: tab === "models" ? "2px solid var(--accent-primary)" : "2px solid transparent",
                        color: tab === "models" ? "var(--text-primary)" : "var(--text-muted)",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem"
                    }}
                >
                    <Database size={16} /> Model Registry
                </button>
            </div>

            {tab === "logs" && (
                <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
                        <thead>
                            <tr style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)" }}>
                                <th style={{ padding: "1rem" }}>Event Type</th>
                                <th style={{ padding: "1rem" }}>User ID</th>
                                <th style={{ padding: "1rem" }}>IP Address</th>
                                <th style={{ padding: "1rem" }}>Details</th>
                                <th style={{ padding: "1rem" }}>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log) => (
                                <tr key={log.id} style={{ borderBottom: "1px solid var(--border)" }}>
                                    <td style={{ padding: "1rem" }}>
                                        <span className="badge badge-neutral" style={{ textTransform: "uppercase", fontSize: "0.65rem" }}>
                                            {log.event_type}
                                        </span>
                                    </td>
                                    <td className="mono" style={{ padding: "1rem", color: "var(--text-secondary)", fontSize: "0.75rem" }}>
                                        {log.user_id ? log.user_id.substring(0, 8) + "..." : "System"}
                                    </td>
                                    <td style={{ padding: "1rem", color: "var(--text-muted)" }}>{log.ip_address || "N/A"}</td>
                                    <td style={{ padding: "1rem", color: "var(--text-secondary)" }}>
                                        <pre style={{ fontSize: "0.7rem", margin: 0, whiteSpace: "pre-wrap" }}>
                                            {JSON.stringify(log.details)}
                                        </pre>
                                    </td>
                                    <td style={{ padding: "1rem", color: "var(--text-muted)" }}>
                                        {new Date(log.occurred_at).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {tab === "models" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.5rem" }}>
                    {models.map((model) => (
                        <div key={model.id} className="card">
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                                <div>
                                    <h3 style={{ fontSize: "1rem", fontWeight: 700 }}>{model.model_name}</h3>
                                    <p style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{model.version_tag} · {model.architecture}</p>
                                </div>
                                {model.is_active ? (
                                    <span className="badge badge-success">Active</span>
                                ) : (
                                    <span className="badge badge-neutral">Archived</span>
                                )}
                            </div>

                            <div style={{ background: "var(--bg-surface)", padding: "0.75rem", borderRadius: "var(--radius-md)", marginBottom: "1rem" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                    <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Evaluation F1-Score</span>
                                    <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-primary)" }}>
                                        {model.f1_score ? (model.f1_score * 100).toFixed(1) + "%" : "N/A"}
                                    </span>
                                </div>
                                <div style={{ height: "4px", background: "var(--border)", borderRadius: "2px", overflow: "hidden" }}>
                                    <div style={{
                                        width: `${(model.f1_score || 0) * 100}%`,
                                        height: "100%",
                                        background: "var(--accent-primary)"
                                    }}></div>
                                </div>
                            </div>

                            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                                Registered: {new Date(model.registered_at).toLocaleDateString()}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
