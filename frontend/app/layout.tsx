import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "ForensicML — Evidence Tampering Detection",
    description:
        "Forensic-grade machine learning platform for detecting tampering in digital images and videos. MSc Cyber Security — CMM500.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
