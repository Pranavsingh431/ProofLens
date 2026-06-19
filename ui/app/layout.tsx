import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ProofLens — Multi-Agent Visual Evidence Verification",
  description:
    "10-component multi-agent pipeline for visual damage claim verification. " +
    "Powered by Gemini 2.5 Flash, deterministic decision engine, and autonomous audit recovery.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className="bg-[rgb(2_8_23)] text-slate-100 antialiased overflow-hidden h-screen">
        {children}
      </body>
    </html>
  );
}
