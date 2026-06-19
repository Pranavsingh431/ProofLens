"use client";

import { useState, useCallback, useRef } from "react";
import type { PipelineStep, OutputRow, PipelineEvent, StepStatus } from "@/types";
import { PIPELINE_STEPS } from "@/lib/steps";
import { streamPipeline } from "@/lib/api";
import PipelineStepCard from "./PipelineStepCard";

const INITIAL_STEPS = (): PipelineStep[] =>
  PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" }));

const STATUS_CONFIG = {
  supported: {
    label: "Supported",
    sublabel: "Claim is supported by visual evidence",
    bg: "from-emerald-950/80 to-emerald-900/20",
    border: "border-emerald-500/30",
    text: "text-emerald-300",
    badge: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
    icon: "✓",
    iconBg: "bg-emerald-500/20 text-emerald-300",
  },
  contradicted: {
    label: "Contradicted",
    sublabel: "Images contradict the damage claim",
    bg: "from-red-950/80 to-red-900/20",
    border: "border-red-500/30",
    text: "text-red-300",
    badge: "bg-red-500/15 border-red-500/30 text-red-300",
    icon: "✕",
    iconBg: "bg-red-500/20 text-red-300",
  },
  not_enough_information: {
    label: "Insufficient Evidence",
    sublabel: "Images do not provide enough evidence",
    bg: "from-amber-950/60 to-amber-900/10",
    border: "border-amber-500/25",
    text: "text-amber-300",
    badge: "bg-amber-500/15 border-amber-500/30 text-amber-300",
    icon: "?",
    iconBg: "bg-amber-500/20 text-amber-300",
  },
} as const;

const SEVERITY_COLORS: Record<string, string> = {
  high:    "text-red-400 bg-red-500/10 border-red-500/25",
  medium:  "text-amber-400 bg-amber-500/10 border-amber-500/25",
  low:     "text-emerald-400 bg-emerald-500/10 border-emerald-500/25",
  none:    "text-slate-500 bg-slate-700/30 border-slate-600/30",
  unknown: "text-slate-500 bg-slate-700/30 border-slate-600/30",
};

interface Props {
  claimId: number;
  userId: string;
  claimObject: string;
  userClaim: string;
  imageCount: number;
  onStepUpdate: (stepId: string, status: StepStatus, isRunning: boolean) => void;
  onRunStart: () => void;
  onRunComplete: (durationMs: number) => void;
}

const OBJECT_ICONS: Record<string, string> = { car: "🚗", laptop: "💻", package: "📦" };
const OBJECT_COLORS: Record<string, string> = {
  car:     "bg-sky-500/10 text-sky-300 border-sky-500/25",
  laptop:  "bg-violet-500/10 text-violet-300 border-violet-500/25",
  package: "bg-orange-500/10 text-orange-300 border-orange-500/25",
};

export default function PipelineRunner({
  claimId, userId, claimObject, userClaim, imageCount,
  onStepUpdate, onRunStart, onRunComplete,
}: Props) {
  const [steps, setSteps]     = useState<PipelineStep[]>(INITIAL_STEPS());
  const [result, setResult]   = useState<OutputRow | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [hasRun, setHasRun]   = useState(false);
  const cleanupRef            = useRef<(() => void) | null>(null);
  const startTimeRef          = useRef<number>(0);

  const handleEvent = useCallback((event: PipelineEvent) => {
    if (event.type === "step_start") {
      setSteps((prev) =>
        prev.map((s) => (s.id === event.step ? { ...s, status: "running" } : s))
      );
      onStepUpdate(event.step, "running", true);
    } else if (event.type === "step_complete") {
      setSteps((prev) =>
        prev.map((s) =>
          s.id === event.step
            ? { ...s, status: "complete", data: event.data, duration_ms: event.duration_ms }
            : s
        )
      );
      onStepUpdate(event.step, "complete", true);
    } else if (event.type === "step_skipped") {
      setSteps((prev) =>
        prev.map((s) => (s.id === event.step ? { ...s, status: "skipped" } : s))
      );
      onStepUpdate(event.step, "skipped", true);
    } else if (event.type === "pipeline_complete") {
      setResult(event.output);
      const duration = Date.now() - startTimeRef.current;
      setIsRunning(false);
      onRunComplete(duration);
    } else if (event.type === "error") {
      setError(event.message);
      setSteps((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "error" } : s))
      );
      setIsRunning(false);
      onRunComplete(Date.now() - startTimeRef.current);
    }
  }, [onStepUpdate, onRunComplete]);

  const runPipeline = useCallback(() => {
    if (cleanupRef.current) cleanupRef.current();
    setSteps(INITIAL_STEPS());
    setResult(null);
    setError(null);
    setIsRunning(true);
    setHasRun(true);
    startTimeRef.current = Date.now();
    onRunStart();

    cleanupRef.current = streamPipeline(
      claimId,
      handleEvent,
      () => setIsRunning(false),
      () => { setError("Connection error — is the backend running?"); setIsRunning(false); }
    );
  }, [claimId, handleEvent, onRunStart]);

  const completeCount  = steps.filter((s) => s.status === "complete").length;
  const progressPct    = Math.round((completeCount / steps.length) * 100);

  return (
    <div className="flex flex-col h-full">

      {/* ── Claim info strip ──────────────────────────────────────── */}
      <div className="shrink-0 px-5 py-4 border-b border-slate-800">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-mono text-slate-500">{userId}</span>
              <span className={`inline-flex items-center gap-1 text-[10px] font-semibold
                px-2 py-0.5 rounded-full border ${OBJECT_COLORS[claimObject] ?? ""}`}>
                {OBJECT_ICONS[claimObject] ?? "◈"} {claimObject}
              </span>
              <span className="text-[10px] text-slate-600">
                {imageCount} image{imageCount !== 1 ? "s" : ""}
              </span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed line-clamp-2">{userClaim}</p>
          </div>
        </div>
      </div>

      {/* ── Run button + progress ─────────────────────────────────── */}
      <div className="shrink-0 px-5 py-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={runPipeline}
            disabled={isRunning}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold
              transition-all duration-200 shadow-sm
              ${isRunning
                ? "bg-slate-700/60 text-slate-500 cursor-not-allowed border border-slate-600/40"
                : "bg-blue-600 hover:bg-blue-500 text-white border border-blue-500/50 shadow-blue-500/20 hover:shadow-md hover:shadow-blue-500/25"
              }`}
          >
            {isRunning ? (
              <>
                <span className="w-3.5 h-3.5 rounded-full border-2 border-slate-500/40 border-t-slate-400 animate-spin" />
                <span>Running…</span>
              </>
            ) : (
              <>
                <span>▶</span>
                <span>{hasRun ? "Re-run" : "Run Pipeline"}</span>
              </>
            )}
          </button>

          {/* Progress bar */}
          {hasRun && (
            <div className="flex-1 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${progressPct}%`,
                    background: result
                      ? "linear-gradient(90deg, #10b981, #34d399)"
                      : "linear-gradient(90deg, #3b82f6, #22d3ee)",
                  }}
                />
              </div>
              <span className="text-[10px] font-mono text-slate-600 shrink-0">
                {completeCount}/{steps.length}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Error banner ─────────────────────────────────────────── */}
      {error && (
        <div className="shrink-0 mx-5 mt-4 px-4 py-3 rounded-xl
          bg-red-500/8 border border-red-500/25 text-red-300 text-xs">
          ⚠ {error}
        </div>
      )}

      {/* ── Steps ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-2">
        {steps.map((step, i) => (
          <PipelineStepCard key={step.id} step={step} index={i} />
        ))}
      </div>

      {/* ── Verdict ────────────────────────────────────────────────── */}
      {result && <VerdictCard result={result} />}
    </div>
  );
}

function VerdictCard({ result }: { result: OutputRow }) {
  const [showAll, setShowAll] = useState(false);
  const status = result.claim_status as keyof typeof STATUS_CONFIG;
  const cfg    = STATUS_CONFIG[status] ?? STATUS_CONFIG.not_enough_information;

  const fields: [string, string][] = [
    ["issue_type",       result.issue_type],
    ["object_part",      result.object_part],
    ["severity",         result.severity],
    ["evidence_met",     String(result.evidence_standard_met)],
    ["valid_image",      String(result.valid_image)],
    ["risk_flags",       result.risk_flags],
    ["supporting_ids",   result.supporting_image_ids],
    ["evidence_reason",  result.evidence_standard_met_reason],
    ["justification",    result.claim_status_justification],
  ];

  const sevColor = SEVERITY_COLORS[result.severity] ?? SEVERITY_COLORS.unknown;

  return (
    <div className={`shrink-0 mx-5 mb-5 mt-2 rounded-xl border bg-gradient-to-b ${cfg.bg} ${cfg.border} overflow-hidden animate-slide-up`}>
      {/* Verdict header */}
      <div className="px-5 py-4 flex items-center gap-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold shrink-0 ${cfg.iconBg}`}>
          {cfg.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-base font-bold ${cfg.text}`}>{cfg.label}</p>
          <p className="text-xs text-slate-500 leading-tight mt-0.5">{cfg.sublabel}</p>
        </div>
        <span className={`px-2.5 py-1 rounded-lg border text-xs font-semibold shrink-0 ${sevColor}`}>
          {result.severity}
        </span>
      </div>

      {/* Fields */}
      <div className="px-5 pb-4 space-y-1.5">
        {(showAll ? fields : fields.slice(0, 5)).map(([k, v]) => (
          <div key={k} className="flex gap-3 text-xs min-w-0">
            <span className="text-slate-500 font-mono w-32 shrink-0">{k}</span>
            <span className="text-slate-300 font-mono truncate" title={v}>{v || "—"}</span>
          </div>
        ))}
        <button
          onClick={() => setShowAll((s) => !s)}
          className="text-[10px] text-slate-600 hover:text-slate-400 mt-1"
        >
          {showAll ? "▲ Show less" : `▼ Show all ${fields.length} fields`}
        </button>
      </div>
    </div>
  );
}
