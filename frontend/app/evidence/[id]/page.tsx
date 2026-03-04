"use client";
import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { evidenceApi, analysisApi } from "@/lib/api";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";
import {
    ShieldAlert, ShieldCheck, Clock, Play,
    ArrowLeft, Copy, CheckCheck, Activity,
} from "lucide-react";

interface FrameResult {
    frame_no: number;
    is_tampered: boolean;
    confidence: number;
}

interface AnalysisResult {
    id: string;
    is_tampered: boolean | null;
    confidence_score: number | null;
    processing_time_s: number | null;
    ela_heatmap_key: string | null;
    frame_results: FrameResult[] | null;
    created_at: string;
}

interface EvidenceDetail {
    id: string;
    filename: string;
    media_type: string;
    status: string;
    sha256_hash: string;
    file_size: number;
    uploaded_at: string;
    mime_type: string;
}

export default function EvidenceDetailPage() {
    const params = useParams();
    const router = useRouter();
    const id = params.id as string;

    const [evidence, setEvidence] = useState<EvidenceDetail | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [analysing, setAnalysing] = useState(false);
    const [copied, setCopied] = useState(false);
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Clean up polling on unmount
    useEffect(() => {
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, []);

    useEffect(() => {
        loadEvidence();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    const loadEvidence = async () => {
        try {
            const { data } = await evidenceApi.get(id);
            setEvidence(data);
        } catch {
            router.push("/dashboard");
        }
    };

    const startAnalysis = async () => {
        if (!evidence) return;
        setAnalysing(true);
        try {
            const { data } = await analysisApi.trigger(evidence.id);
            const resultId: string = data.result_id;

            // Poll every 3 seconds until result is ready
            pollRef.current = setInterval(async () => {
                try {
                    const { data: res } = await analysisApi.getResult(resultId);
                    if (res.is_tampered !== null && res.is_tampered !== undefined) {
                        setResult(res);
                        setAnalysing(false);
                        if (pollRef.current) clearInterval(pollRef.current);
                        // Refresh evidence status
                        const { data: evData } = await evidenceApi.get(id);
                        setEvidence(evData);
                    }
                } catch {
                    // Result not ready yet — keep polling
                }
            }, 3000);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })
                ?.response?.data?.detail || "Failed to start analysis";
            alert(msg);
            setAnalysing(false);
        }
    };

    const copyHash = () => {
        if (evidence) {
            navigator.clipboard.writeText(evidence.sha256_hash);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (!evidence) {
        return (
            <div style={{
                minHeight: "100vh", display: "flex",
                alignItems: "center", justifyContent: "center",
            }}>
                <p style={{ color: "var(--text-muted)" }} className="pulsing">Loading evidence…</p>
            </div>
        );
    }

    const isTampered = result?.is_tampered;
    const confidence = result?.confidence_score ?? 0;
    const frameData = result?.frame_results ?? [];

    return (
        <div className="page-container animate-in" style={{ maxWidth: 900 }}>
            {/* Back */}
            <button
                className="btn btn-ghost"
                style={{ marginBottom: "1.5rem" }}
                onClick={() => router.push("/dashboard")}
            >
                <ArrowLeft size={16} /> Back to Dashboard
            </button>

            {/* ── Evidence Header Card ──────────────────────────────────────────── */}
            <div className="card" style={{ marginBottom: "1.5rem" }}>
                <div style={{
                    display: "flex", justifyContent: "space-between",
                    alignItems: "flex-start", flexWrap: "wrap", gap: "1rem",
                }}>
                    <div>
                        <h1 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.25rem" }}>
                            {evidence.filename}
                        </h1>
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                            {evidence.mime_type} · {(evidence.file_size / 1024 / 1024).toFixed(2)} MB
                            · {evidence.media_type}
                            · Uploaded {new Date(evidence.uploaded_at).toLocaleString()}
                        </p>
                    </div>

                    {/* Analysis trigger */}
                    {!analysing && !result && (
                        <button className="btn btn-primary" onClick={startAnalysis}>
                            <Play size={15} /> Run Analysis
                        </button>
                    )}
                    {analysing && (
                        <span className="btn btn-ghost" style={{ cursor: "default" }}>
                            <Activity size={15} className="pulsing" /> Analysing…
                        </span>
                    )}
                </div>

                {/* SHA-256 integrity hash */}
                <div style={{
                    marginTop: "1rem",
                    padding: "0.75rem 1rem",
                    background: "var(--bg-surface)",
                    borderRadius: "var(--radius-md)",
                    display: "flex", justifyContent: "space-between",
                    alignItems: "center", gap: "1rem",
                }}>
                    <div style={{ overflow: "hidden" }}>
                        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: 2 }}>
                            SHA-256 Integrity Hash
                        </p>
                        <code className="mono" style={{
                            fontSize: "0.78rem", color: "var(--text-secondary)",
                            wordBreak: "break-all",
                        }}>
                            {evidence.sha256_hash}
                        </code>
                    </div>
                    <button className="btn btn-ghost" style={{ flexShrink: 0 }} onClick={copyHash}>
                        {copied ? <><CheckCheck size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
                    </button>
                </div>
            </div>

            {/* ── No result yet ────────────────────────────────────────────────── */}
            {!result && !analysing && (
                <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
                    <Clock size={36} color="var(--text-muted)" style={{ margin: "0 auto 1rem" }} />
                    <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
                        No forensic analysis has been run on this evidence yet.
                    </p>
                    <button className="btn btn-primary" onClick={startAnalysis}>
                        <Play size={15} /> Start Forensic Analysis
                    </button>
                </div>
            )}

            {/* ── Polling state ────────────────────────────────────────────────── */}
            {analysing && !result && (
                <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
                    <Activity size={36} color="var(--accent-primary)"
                        style={{ margin: "0 auto 1rem" }} className="pulsing" />
                    <p style={{ color: "var(--text-secondary)" }}>
                        ML inference in progress — polling every 3 seconds…
                    </p>
                </div>
            )}

            {/* ── Verdict Card ─────────────────────────────────────────────────── */}
            {result && (
                <>
                    <div className="card animate-in" style={{
                        marginBottom: "1.5rem",
                        borderColor: isTampered ? "var(--accent-danger)" : "var(--accent-success)",
                        background: isTampered ? "#f9707010" : "#52d17c10",
                    }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem", flexWrap: "wrap" }}>
                            {isTampered
                                ? <ShieldAlert size={44} color="var(--accent-danger)" />
                                : <ShieldCheck size={44} color="var(--accent-success)" />}
                            <div>
                                <h2 style={{
                                    fontSize: "1.5rem", fontWeight: 800,
                                    color: isTampered ? "var(--accent-danger)" : "var(--accent-success)",
                                }}>
                                    {isTampered ? "⚠ TAMPERING DETECTED" : "✓ AUTHENTIC"}
                                </h2>
                                <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                                    Confidence: <strong>{(confidence * 100).toFixed(1)}%</strong>
                                    {result.processing_time_s != null &&
                                        ` · Processed in ${result.processing_time_s.toFixed(2)}s`}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* ── ELA Heatmap ────────────────────────────────────────────── */}
                    {result.ela_heatmap_key && (
                        <div className="card animate-in" style={{ marginBottom: "1.5rem" }}>
                            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.5rem" }}>
                                Error Level Analysis (ELA) Heatmap
                            </h3>
                            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                                Brighter regions indicate areas with inconsistent compression — a forensic
                                indicator of manipulation or splicing.
                            </p>
                            {/* Heatmap served via presigned URL redirect from the backend */}
                            <img
                                src={`/api/v1/analysis/${result.id}/heatmap`}
                                alt="ELA Heatmap"
                                style={{
                                    width: "100%",
                                    borderRadius: "var(--radius-md)",
                                    border: "1px solid var(--border)",
                                }}
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = "none";
                                }}
                            />
                        </div>
                    )}

                    {/* ── Frame Timeline (video only) ─────────────────────────────── */}
                    {frameData.length > 0 && (
                        <div className="card animate-in" style={{ marginBottom: "1.5rem" }}>
                            <h3 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                                Frame-Level Tampering Timeline
                            </h3>
                            <p style={{ color: "var(--text-secondary)", fontSize: "0.83rem", marginBottom: "1rem" }}>
                                Per-frame confidence from CNN+LSTM temporal analysis.
                                Bars above the 0.5 threshold line indicate suspected tampering.
                            </p>
                            <ResponsiveContainer width="100%" height={230}>
                                <BarChart data={frameData} margin={{ top: 5, right: 10, bottom: 20, left: 0 }}>
                                    <XAxis
                                        dataKey="frame_no"
                                        tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                                        label={{ value: "Frame #", position: "insideBottom", offset: -10, fill: "var(--text-muted)", fontSize: 11 }}
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
                                        }}
                                        formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Confidence"]}
                                        labelFormatter={(label: number) => `Frame #${label}`}
                                    />
                                    <ReferenceLine
                                        y={0.5}
                                        stroke="var(--accent-warn)"
                                        strokeDasharray="4 3"
                                        label={{ value: "Threshold", fill: "var(--accent-warn)", fontSize: 10 }}
                                    />
                                    <Bar dataKey="confidence" radius={[3, 3, 0, 0]}>
                                        {frameData.map((f: FrameResult, i: number) => (
                                            <Cell
                                                key={i}
                                                fill={f.is_tampered ? "var(--accent-danger)" : "var(--accent-success)"}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                                🔴 Tampered frames &nbsp;·&nbsp; 🟢 Authentic frames
                            </p>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
