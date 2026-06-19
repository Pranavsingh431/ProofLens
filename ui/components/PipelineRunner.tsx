"use client";

import { useState, useCallback } from "react";
import type { PipelineStep, OutputRow, PipelineEvent } from "@/types";
import { PIPELINE_STEPS } from "@/lib/steps";
import { streamPipeline } from "@/lib/api";
import PipelineStepCard from "./PipelineStepCard";

const INITIAL_STEPS = (): PipelineStep[] =>
  PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" }));

const STATUS_CONFIG = {
  supported: {
    label: "Supported",
    bg: "bg-emerald-900/40 border-emerald-500/60",
    text: "text-emerald-300",
    dot: "bg-emerald-500",
  },
  contradicted: {
    label: "Contradicted",
    bg: "bg-red-900/40 border-red-500/60",
    text: "text-red-300",
    dot: "bg-red-500",
  },
  not_enough_information: {
    label: "Not Enough Information",
    bg: "bg-yellow-900/30 border-yellow-500/50",
    text: "text-yellow-300",
    dot: "bg-yellow-500",
  },
} as const;

interface Props {
  claimId: number;
  userId: string;
  claimObject: string;
  userClaim: string;
  imageCount: number;
}

export default function PipelineRunner({
  claimId,
  userId,
  claimObject,
  userClaim,
  imageCount,
}: Props) {
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS());
  const [result, setResult] = useState<OutputRow | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cleanupFn, setCleanupFn] = useState<(() => void) | null>(null);

  const handleEvent = useCallback((event: PipelineEvent) => {
    if (event.type === "step_start") {
      setSteps((prev) =>
        prev.map((s) => (s.id === event.step ? { ...s, status: "running" } : s))
      );
    } else if (event.type === "step_complete") {
      setSteps((prev) =>
        prev.map((s) =>
          s.id === event.step
            ? { ...s, status: "complete", data: event.data, duration_ms: event.duration_ms }
            : s
        )
      );
    } else if (event.type === "step_skipped") {
      setSteps((prev) =>
        prev.map((s) => (s.id === event.step ? { ...s, status: "skipped" } : s))
      );
    } else if (event.type === "pipeline_complete") {
      setResult(event.output);
    } else if (event.type === "error") {
      setError(event.message);
      setSteps((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "error" } : s))
      );
    }
  }, []);

  const runPipeline = useCallback(() => {
    if (cleanupFn) cleanupFn();
    setSteps(INITIAL_STEPS());
    setResult(null);
    setError(null);
    setIsRunning(true);

    const cleanup = streamPipeline(
      claimId,
      handleEvent,
      () => setIsRunning(false),
      () => setError("Connection error — is the backend running?")
    );
    setCleanupFn(() => cleanup);
  }, [claimId, handleEvent, cleanupFn]);

  const objectColors: Record<string, string> = {
    car:     "bg-blue-900/40 text-blue-300 border-blue-700/50",
    laptop:  "bg-purple-900/40 text-purple-300 border-purple-700/50",
    package: "bg-orange-900/40 text-orange-300 border-orange-700/50",
  };

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Claim header */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-slate-400 text-sm font-mono">{userId}</span>
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded border ${objectColors[claimObject] ?? "bg-slate-700 text-slate-300 border-slate-600"}`}
          >
            {claimObject}
          </span>
          <span className="text-slate-500 text-xs">
            {imageCount} image{imageCount !== 1 ? "s" : ""}
          </span>
        </div>
        <p className="text-slate-300 text-sm leading-relaxed line-clamp-3">{userClaim}</p>
      </div>

      {/* Run button */}
      <button
        onClick={runPipeline}
        disabled={isRunning}
        className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg
          bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500
          text-white font-semibold text-sm transition-colors"
      >
        {isRunning ? (
          <>
            <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
            Running pipeline…
          </>
        ) : (
          <>▶ Run Pipeline</>
        )}
      </button>

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm">
          ⚠ {error}
        </div>
      )}

      {/* Pipeline steps */}
      <div className="space-y-2 overflow-y-auto flex-1 pr-1">
        {steps.map((step, i) => (
          <PipelineStepCard key={step.id} step={step} index={i} />
        ))}
      </div>

      {/* Final result */}
      {result && <ResultCard result={result} />}
    </div>
  );
}

function ResultCard({ result }: { result: OutputRow }) {
  const [showAll, setShowAll] = useState(false);
  const status = result.claim_status as keyof typeof STATUS_CONFIG;
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.not_enough_information;

  const fields: [string, string][] = [
    ["issue_type",           result.issue_type],
    ["object_part",          result.object_part],
    ["severity",             result.severity],
    ["evidence_standard_met", String(result.evidence_standard_met)],
    ["valid_image",          String(result.valid_image)],
    ["risk_flags",           result.risk_flags],
    ["supporting_image_ids", result.supporting_image_ids],
    ["evidence_reason",      result.evidence_standard_met_reason],
    ["justification",        result.claim_status_justification],
  ];

  return (
    <div className={`rounded-xl border p-4 ${cfg.bg}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-2.5 h-2.5 rounded-full ${cfg.dot}`} />
        <span className={`font-bold text-base ${cfg.text}`}>{cfg.label}</span>
        <span className="text-slate-400 text-xs ml-auto">Final result</span>
      </div>

      <div className="space-y-1.5">
        {(showAll ? fields : fields.slice(0, 5)).map(([k, v]) => (
          <div key={k} className="flex gap-2 text-xs min-w-0">
            <span className="text-slate-400 font-mono shrink-0 w-36">{k}</span>
            <span
              className="text-slate-200 font-mono truncate"
              title={v}
            >
              {v || "—"}
            </span>
          </div>
        ))}
      </div>

      {fields.length > 5 && (
        <button
          onClick={() => setShowAll((s) => !s)}
          className="mt-2 text-xs text-slate-400 hover:text-slate-200"
        >
          {showAll ? "Show less ▲" : `Show all ${fields.length} fields ▼`}
        </button>
      )}
    </div>
  );
}
