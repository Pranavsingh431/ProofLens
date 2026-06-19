"use client";

import { useState } from "react";
import type { PipelineStep } from "@/types";

interface Props {
  step: PipelineStep;
  index: number;
}

const STATUS_STYLES: Record<string, { dot: string; text: string; ring: string; bg: string }> = {
  pending:  { dot: "bg-slate-700",    text: "text-slate-600",  ring: "",                          bg: "" },
  running:  { dot: "bg-blue-400",     text: "text-blue-300",   ring: "ring-1 ring-blue-500/30",   bg: "bg-blue-500/5" },
  complete: { dot: "bg-emerald-400",  text: "text-emerald-300",ring: "ring-1 ring-emerald-500/20",bg: "bg-emerald-500/5" },
  skipped:  { dot: "bg-slate-700",    text: "text-slate-600",  ring: "",                          bg: "" },
  error:    { dot: "bg-red-400",      text: "text-red-300",    ring: "ring-1 ring-red-500/30",    bg: "bg-red-500/5" },
};

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (Array.isArray(v)) return v.length === 0 ? "[]" : v.join(", ");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

const HIGHLIGHT_KEYS = new Set([
  "claimed_issue", "claimed_part", "claim_status", "language", "path",
  "evidence_standard_met", "target_part_visible", "damage_consistent",
  "evidence_coverage_score", "risk_flags", "passed",
]);

function DataEntry({ k, v }: { k: string; v: unknown }) {
  const display = formatValue(v);
  const isHighlighted = HIGHLIGHT_KEYS.has(k);
  const isBool = typeof v === "boolean";
  return (
    <div className="flex items-start gap-2.5 py-1 border-b border-slate-700/30 last:border-0">
      <span className={`text-[11px] font-mono shrink-0 w-44 ${
        isHighlighted ? "text-slate-300" : "text-slate-500"
      }`}>{k}</span>
      <span className={`text-[11px] font-mono break-all ${
        isBool
          ? (v ? "text-emerald-400" : "text-red-400")
          : isHighlighted
            ? "text-cyan-300"
            : "text-slate-400"
      }`}>{display}</span>
    </div>
  );
}

export default function PipelineStepCard({ step, index }: Props) {
  const [expanded, setExpanded] = useState(false);
  const s = STATUS_STYLES[step.status] ?? STATUS_STYLES.pending;
  const isRunning  = step.status === "running";
  const isComplete = step.status === "complete";
  const hasData    = isComplete && step.data && Object.keys(step.data).length > 0;

  return (
    <div className={`rounded-xl border transition-all duration-300 overflow-hidden ${
      isRunning
        ? "border-blue-500/30 bg-blue-500/5 shadow-md shadow-blue-500/10"
        : isComplete
          ? "border-emerald-500/15 bg-emerald-500/5"
          : "border-slate-700/30 bg-slate-800/20"
    }`}>
      {/* Header row */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Index bubble */}
        <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold
          transition-colors ${
            isRunning  ? "bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/40" :
            isComplete ? "bg-emerald-500/20 text-emerald-300" :
                         "bg-slate-700/60 text-slate-600"
          }`}>
          {isRunning ? (
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          ) : isComplete ? (
            <span className="text-emerald-400">✓</span>
          ) : (
            <span>{index + 1}</span>
          )}
        </div>

        {/* Step info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold leading-none ${s.text}`}>
              {step.icon} {step.label}
            </span>
            {step.layer && (
              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border
                ${isRunning  ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                  isComplete ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
                               "bg-slate-700/50 text-slate-600 border-slate-600/30"}`}>
                {step.layer}
              </span>
            )}
          </div>
          {!isRunning && (
            <p className="text-[10px] text-slate-600 leading-tight mt-0.5">{step.description}</p>
          )}
          {isRunning && (
            <p className="text-[10px] text-blue-400/70 leading-tight mt-0.5 animate-pulse">Processing…</p>
          )}
        </div>

        {/* Right: duration + expand */}
        <div className="flex items-center gap-2 shrink-0">
          {step.duration_ms !== undefined && (
            <span className="text-[10px] font-mono text-slate-600">
              {step.duration_ms < 1000
                ? `${step.duration_ms}ms`
                : `${(step.duration_ms / 1000).toFixed(1)}s`}
            </span>
          )}
          {hasData && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="w-5 h-5 rounded flex items-center justify-center
                text-slate-600 hover:text-slate-300 hover:bg-slate-700/50 transition-all text-[10px]"
            >
              {expanded ? "▲" : "▼"}
            </button>
          )}
        </div>
      </div>

      {/* Expanded data */}
      {expanded && hasData && (
        <div className="px-4 pb-3 pt-1 border-t border-slate-700/30 animate-fade-in">
          <div className="bg-slate-900/60 rounded-lg p-3">
            {Object.entries(step.data!).map(([k, v]) => (
              <DataEntry key={k} k={k} v={v} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
