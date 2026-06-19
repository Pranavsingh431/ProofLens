"use client";

import { useState } from "react";
import type { PipelineStep } from "@/types";

interface Props {
  step: PipelineStep;
  index: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending:  "text-slate-500",
  running:  "text-yellow-400",
  complete: "text-emerald-400",
  skipped:  "text-slate-500",
  error:    "text-red-400",
};

const STATUS_BG: Record<string, string> = {
  pending:  "bg-slate-800 border-slate-700",
  running:  "bg-slate-800 border-yellow-500/60",
  complete: "bg-slate-800 border-emerald-500/40",
  skipped:  "bg-slate-800/50 border-slate-700/50",
  error:    "bg-slate-800 border-red-500/60",
};

const STATUS_ICON: Record<string, string> = {
  pending:  "○",
  running:  "◌",
  complete: "●",
  skipped:  "–",
  error:    "✕",
};

function DataRow({ k, v }: { k: string; v: unknown }) {
  if (v === null || v === undefined) return null;
  const display =
    typeof v === "object" ? JSON.stringify(v, null, 0) : String(v);
  const tooLong = display.length > 80;
  return (
    <div className="flex gap-2 min-w-0 text-xs">
      <span className="text-slate-400 shrink-0 min-w-[140px] font-mono">{k}</span>
      <span className="text-slate-200 font-mono truncate" title={display}>
        {tooLong ? display.slice(0, 80) + "…" : display}
      </span>
    </div>
  );
}

export default function PipelineStepCard({ step, index }: Props) {
  const [expanded, setExpanded] = useState(false);
  const hasData = step.data && Object.keys(step.data).length > 0;
  const isRunning = step.status === "running";

  return (
    <div
      className={`rounded-lg border px-4 py-3 transition-all duration-300 ${STATUS_BG[step.status]}`}
    >
      <div className="flex items-center gap-3">
        {/* step number */}
        <span className="text-slate-500 text-xs font-mono w-5 shrink-0">{index + 1}</span>

        {/* status icon */}
        <span
          className={`text-sm font-bold ${STATUS_COLORS[step.status]} ${isRunning ? "animate-pulse" : ""} w-4 shrink-0`}
        >
          {STATUS_ICON[step.status]}
        </span>

        {/* layer badge */}
        <span className="text-[10px] font-mono text-slate-500 bg-slate-700 px-1.5 py-0.5 rounded shrink-0">
          {step.layer}
        </span>

        {/* emoji + label */}
        <span className="text-sm mr-1">{step.icon}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold ${STATUS_COLORS[step.status]}`}>{step.label}</p>
          <p className="text-xs text-slate-500 leading-tight">{step.description}</p>
        </div>

        {/* duration */}
        {step.duration_ms !== undefined && (
          <span className="text-[10px] font-mono text-slate-500 shrink-0">
            {step.duration_ms < 1000
              ? `${step.duration_ms}ms`
              : `${(step.duration_ms / 1000).toFixed(1)}s`}
          </span>
        )}

        {/* expand toggle */}
        {hasData && step.status === "complete" && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-slate-400 hover:text-slate-200 text-xs shrink-0 ml-1"
          >
            {expanded ? "▲" : "▼"}
          </button>
        )}
      </div>

      {/* expanded data */}
      {expanded && hasData && (
        <div className="mt-3 pl-10 space-y-1 border-t border-slate-700 pt-2">
          {Object.entries(step.data!).map(([k, v]) => (
            <DataRow key={k} k={k} v={v} />
          ))}
        </div>
      )}
    </div>
  );
}
