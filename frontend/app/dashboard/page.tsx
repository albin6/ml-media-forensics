"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { evidenceApi, analysisApi } from "@/lib/api";
import { logout, isAuthenticated } from "@/lib/auth";
import {
    ShieldCheck, Upload, LogOut, FileImage, Film,
    CheckCircle, XCircle, Clock, Activity, AlertTriangle
} from "lucide-react";

interface Evidence {
    id: string; filename: string; media_type: string;
    status: string; sha256_hash: string; uploaded_at: string; file_size: number;
}

function formatBytes(b: number) {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function StatusBadge({ status }: { status: string }) {
    const map: Record<string, { icon: any; label: string; cls: string }> = {
        pending: { icon: Clock, label: "Pending", cls: "badge-warn" },
        processing: { icon: Activity, label: "Analysing", cls: "badge-neutral" },
        completed: { icon: CheckCircle, label: "Completed", cls: "badge-success" },
        failed: { icon: XCircle, label: "Failed", cls: "badge-danger" },
    };
    const s = map[status] || map.pending;
    return (
        <span className={`badge ${s.cls}`}>
            <s.icon size={11} /> {s.label}
        </span>
    );
}

export default function DashboardPage() {
    const router = useRouter();
    const [evidence, setEvidence] = useState<Evidence[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [dragActive, setDragActive] = useState(false);

    useEffect(() => {
        if (!isAuthenticated()) { router.push("/login"); return; }
        loadEvidence();
    }, []);

    const loadEvidence = async () => {
        try {
            const { data } = await evidenceApi.list();
            setEvidence(data);
        } catch { router.push("/login"); }
        finally { setLoading(false); }
    };

    const handleFile = async (file: File) => {
        setUploading(true);
        setProgress(0);
        try {
            const { data } = await evidenceApi.upload(file, setProgress);
            await loadEvidence();
            router.push(`/evidence/${data.id}`);
        } catch (err: any) {
            alert(err.response?.data?.detail || "Upload failed");
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    const onDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, []);

    const stats = {
        total: evidence.length,
        tampered: 0,
        completed: evidence.filter(e => e.status === "completed").length,
        pending: evidence.filter(e => e.status === "pending" || e.status === "processing").length,
    };

    return (
        <div style={{ minHeight: "100vh", display: "flex" }}>
            {/* Sidebar */}
            <aside style={{
                width: 240, background: "var(--bg-surface)",
                borderRight: "1px solid var(--border)",
                padding: "1.5rem 1rem",
                display: "flex", flexDirection: "column",
            }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: "2rem" }}>
                    <ShieldCheck size={22} color="var(--accent-primary)" />
                    <span style={{ fontWeight: 700, fontSize: "1rem" }}>ForensicML</span>
                </div>

                <nav style={{ flex: 1 }}>
                    {[
                        { icon: Activity, label: "Dashboard", href: "/dashboard" },
                        { icon: Upload, label: "Upload", href: "/dashboard" },
                    ].map(item => (
                        <button key={item.label}
                            className="btn btn-ghost"
                            style={{ width: "100%", justifyContent: "flex-start", marginBottom: "0.25rem" }}
                            onClick={() => router.push(item.href)}
                        >
                            <item.icon size={16} /> {item.label}
                        </button>
                    ))}
                </nav>

                <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "flex-start" }}
                    onClick={() => logout()}>
                    <LogOut size={16} /> Sign Out
                </button>
            </aside>

            {/* Main */}
            <main style={{ flex: 1, overflow: "auto" }}>
                <div className="page-container">
                    {/* Stats Row */}
                    <div className="grid-3" style={{ marginBottom: "2rem" }}>
                        {[
                            { label: "Total Evidence", value: stats.total, color: "var(--accent-primary)" },
                            { label: "Completed", value: stats.completed, color: "var(--accent-success)" },
                            { label: "Pending", value: stats.pending, color: "var(--accent-warn)" },
                        ].map(s => (
                            <div key={s.label} className="card animate-in">
                                <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.5rem" }}>{s.label}</p>
                                <p style={{ fontSize: "2.5rem", fontWeight: 700, color: s.color }}>{s.value}</p>
                            </div>
                        ))}
                    </div>

                    {/* Upload Zone */}
                    <div className="card" style={{ marginBottom: "2rem" }}>
                        <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem" }}>
                            Upload Evidence
                        </h2>
                        <div
                            className={`dropzone ${dragActive ? "active" : ""}`}
                            onDragOver={e => { e.preventDefault(); setDragActive(true); }}
                            onDragLeave={() => setDragActive(false)}
                            onDrop={onDrop}
                            onClick={() => {
                                const input = document.getElementById("file-input") as HTMLInputElement;
                                input?.click();
                            }}
                        >
                            <input id="file-input" type="file"
                                accept="image/jpeg,image/png,video/mp4"
                                style={{ display: "none" }}
                                onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
                            />
                            {uploading ? (
                                <div>
                                    <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
                                        Uploading and computing SHA-256… {progress}%
                                    </p>
                                    <div style={{ background: "var(--border)", borderRadius: 999, height: 6, overflow: "hidden" }}>
                                        <div style={{ width: `${progress}%`, height: "100%", background: "var(--accent-primary)", transition: "width 0.2s" }} />
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <Upload size={32} color="var(--text-muted)" style={{ margin: "0 auto 1rem" }} />
                                    <p style={{ fontWeight: 500, marginBottom: "0.25rem" }}>
                                        Drop image or video here
                                    </p>
                                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                                        JPEG, PNG up to 50 MB · MP4 up to 2 GB
                                    </p>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Evidence Table */}
                    <div className="card">
                        <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem" }}>
                            Evidence Records
                        </h2>
                        {loading ? (
                            <p style={{ color: "var(--text-muted)" }} className="pulsing">Loading…</p>
                        ) : evidence.length === 0 ? (
                            <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "2rem" }}>
                                No evidence uploaded yet.
                            </p>
                        ) : (
                            <div style={{ overflowX: "auto" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
                                    <thead>
                                        <tr style={{ borderBottom: "1px solid var(--border)" }}>
                                            {["File", "Type", "Size", "SHA-256", "Status", "Uploaded", ""].map(h => (
                                                <th key={h} style={{ padding: "0.75rem 0.5rem", textAlign: "left", color: "var(--text-secondary)", fontWeight: 500 }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {evidence.map(ev => (
                                            <tr key={ev.id}
                                                style={{ borderBottom: "1px solid var(--border)", cursor: "pointer", transition: "background 0.15s" }}
                                                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-card-hover)")}
                                                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                                                onClick={() => router.push(`/evidence/${ev.id}`)}
                                            >
                                                <td style={{ padding: "0.75rem 0.5rem", display: "flex", alignItems: "center", gap: 8 }}>
                                                    {ev.media_type === "image"
                                                        ? <FileImage size={14} color="var(--accent-primary)" />
                                                        : <Film size={14} color="var(--accent-warn)" />}
                                                    <span style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                        {ev.filename}
                                                    </span>
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-secondary)" }}>
                                                    {ev.media_type}
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-secondary)" }}>
                                                    {formatBytes(ev.file_size)}
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem" }}>
                                                    <code className="mono" style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                                                        {ev.sha256_hash.substring(0, 12)}…
                                                    </code>
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem" }}>
                                                    <StatusBadge status={ev.status} />
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                                                    {new Date(ev.uploaded_at).toLocaleDateString()}
                                                </td>
                                                <td style={{ padding: "0.75rem 0.5rem" }}>
                                                    <span style={{ color: "var(--accent-primary)", fontSize: "0.8rem" }}>View →</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
