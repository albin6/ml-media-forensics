"use client";
import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { evidenceApi, analysisApi } from "@/lib/api";
import {
    ShieldAlert, ShieldCheck, Clock, Play,
    ArrowLeft, Copy, CheckCheck, Activity,
} from "lucide-react";

import { ConfidenceGauge } from "@/components/forensics/ConfidenceGauge";
import { ElaHeatmap } from "@/components/forensics/ElaHeatmap";
import { FrameTimeline } from "@/components/forensics/FrameTimeline";

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

            pollRef.current = setInterval(async () => {
                try {
                    const { data: res } = await analysisApi.getResult(resultId);
                    if (res.is_tampered !== null && res.is_tampered !== undefined) {
                        setResult(res);
                        setAnalysing(false);
                        if (pollRef.current) clearInterval(pollRef.current);
                        const { data: evData } = await evidenceApi.get(id);
                        setEvidence(evData);
                    }
                } catch {
                    // Result not ready yet
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
            <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <p style={{ color: "var(--text-muted)" }} className="pulsing">Loading evidence…</p>
            </div>
        );
    }

    const isTampered = result?.is_tampered;
    const confidence = result?.confidence_score ?? 0;
    const frameData = result?.frame_results ?? [];

    return (
        <div className="page-container animate-in" style={{ maxWidth: 900 }}>
            <button className="btn btn-ghost" style={{ marginBottom: "1.5rem" }} onClick={() => router.push("/dashboard")}>
                <ArrowLeft size={16} /> Back to Dashboard
            </button>

            <div className="card" style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                    <div>
                        <h1 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.25rem" }}>{evidence.filename}</h1>
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                            {evidence.mime_type} · {(evidence.file_size / 1024 / 1024).toFixed(2)} MB · {evidence.media_type} · Uploaded {new Date(evidence.uploaded_at).toLocaleString()}
                        </p>
                    </div>
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

                <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", background: "var(--bg-surface)", borderRadius: "var(--radius-md)", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                    <div style={{ overflow: "hidden" }}>
                        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: 2 }}>SHA-256 Integrity Hash</p>
                        <code className="mono" style={{ fontSize: "0.78rem", color: "var(--text-secondary)", wordBreak: "break-all" }}>{evidence.sha256_hash}</code>
                    </div>
                    <button className="btn btn-ghost" style={{ flexShrink: 0 }} onClick={copyHash}>
                        {copied ? <><CheckCheck size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
                    </button>
                </div>
            </div>

            {!result && !analysing && (
                <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
                    <Clock size={36} color="var(--text-muted)" style={{ margin: "0 auto 1rem" }} />
                    <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>No forensic analysis run yet.</p>
                    <button className="btn btn-primary" onClick={startAnalysis}><Play size={15} /> Start Analysis</button>
                </div>
            )}

            {analysing && !result && (
                <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
                    <Activity size={36} color="var(--accent-primary)" style={{ margin: "0 auto 1rem" }} className="pulsing" />
                    <p style={{ color: "var(--text-secondary)" }}>ML inference in progress… polling every 3s</p>
                </div>
            )}

            {result && (
                <>
                    <div className="card animate-in" style={{
                        marginBottom: "1.5rem",
                        borderColor: isTampered ? "var(--accent-danger)" : "var(--accent-success)",
                        background: isTampered ? "#f9707010" : "#52d17c10",
                    }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "2rem", flexWrap: "wrap", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
                                {isTampered ? <ShieldAlert size={44} color="var(--accent-danger)" /> : <ShieldCheck size={44} color="var(--accent-success)" />}
                                <div>
                                    <h2 style={{ fontSize: "1.5rem", fontWeight: 800, color: isTampered ? "var(--accent-danger)" : "var(--accent-success)" }}>
                                        {isTampered ? "⚠ TAMPERING DETECTED" : "✓ AUTHENTIC"}
                                    </h2>
                                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                                        Forensic Assessment Checklist Complete {result.processing_time_s != null && ` · ${result.processing_time_s.toFixed(2)}s`}
                                    </p>
                                </div>
                            </div>
                            <ConfidenceGauge score={confidence} isTampered={!!isTampered} size={100} />
                        </div>
                    </div>

                    <div className="grid-2">
                        {result.ela_heatmap_key && (
                            <div className="card animate-in">
                                <ElaHeatmap id={result.id} filename={evidence.filename} />
                            </div>
                        )}
                        {frameData.length > 0 && (
                            <div className="card animate-in" style={{ gridColumn: result.ela_heatmap_key ? "1 / span 2" : "auto" }}>
                                <FrameTimeline data={frameData} />
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
