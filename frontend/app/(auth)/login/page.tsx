"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";
import { ShieldCheck, Lock, Mail, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPwd, setShowPwd] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await login(email, password);
            router.push("/dashboard");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Invalid credentials");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "radial-gradient(ellipse at 30% 20%, #1a2040 0%, var(--bg-base) 60%)",
            padding: "2rem",
        }}>
            <div style={{ width: "100%", maxWidth: "420px" }} className="animate-in">
                {/* Header */}
                <div style={{ textAlign: "center", marginBottom: "2rem" }}>
                    <div style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: 56, height: 56,
                        borderRadius: "50%",
                        background: "var(--accent-glow)",
                        border: "1px solid var(--accent-primary)",
                        marginBottom: "1rem",
                    }}>
                        <ShieldCheck size={28} color="var(--accent-primary)" />
                    </div>
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
                        ForensicML
                    </h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                        Digital Evidence Tampering Detection
                    </p>
                </div>

                {/* Card */}
                <div className="card">
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1.5rem" }}>
                        Sign in to your account
                    </h2>
                    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                        <div>
                            <label htmlFor="email">Email Address</label>
                            <div style={{ position: "relative" }}>
                                <Mail size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    placeholder="analyst@forensics.local"
                                    style={{ paddingLeft: "2.5rem" }}
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password">Password</label>
                            <div style={{ position: "relative" }}>
                                <Lock size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                                <input
                                    id="password"
                                    type={showPwd ? "text" : "password"}
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    placeholder="••••••••••"
                                    style={{ paddingLeft: "2.5rem", paddingRight: "2.5rem" }}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPwd(p => !p)}
                                    style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
                                >
                                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div style={{
                                background: "var(--accent-danger)15",
                                border: "1px solid var(--accent-danger)50",
                                borderRadius: "var(--radius-md)",
                                padding: "0.75rem 1rem",
                                color: "var(--accent-danger)",
                                fontSize: "0.875rem",
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                            style={{ justifyContent: "center", marginTop: "0.5rem" }}
                        >
                            {loading ? <span className="pulsing">Authenticating…</span> : "Sign In"}
                        </button>
                    </form>
                </div>

                <p style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.75rem", marginTop: "1.5rem" }}>
                    MSc Cyber Security — CMM500 Project · Forensic access only
                </p>
            </div>
        </div>
    );
}
