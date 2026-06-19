import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofLens — Multi-Agent Visual Evidence Verification",
  description:
    "10-component multi-agent pipeline for visual damage claim verification. " +
    "Powered by Gemini 2.5 Flash, deterministic decision engine, and autonomous audit recovery.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="h-screen overflow-hidden bg-[#0B1220] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
