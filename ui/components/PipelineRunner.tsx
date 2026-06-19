"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { OutputRow, PipelineEvent, StepStatus } from "@/types";
import { streamPipeline } from "@/lib/api";
import {
  cleanClaimText,
  evidenceSummary,
  estimateRisk,
  formatField,
  imageNames,
  statusLabel,
  statusTone,
  summarizeClaim,
  supportingImages,
} from "@/lib/presentation";

const TIMELINE = [
  { id: "claim_parser", label: "Claim Parser", steps: ["signal_detection", "claim_parser"] },
  { id: "evidence_requirement", label: "Evidence Rules", steps: ["evidence_requirement"] },
  { id: "vision_analysis", label: "Vision Analysis", steps: ["precheck", "vision_quality"] },
  { id: "quality_check", label: "Quality Check", steps: ["precheck", "vision_quality"] },
  { id: "fusion", label: "Fusion", steps: ["fusion", "object_part_validator"] },
  { id: "risk_assessment", label: "Risk Assessment", steps: ["history_risk"] },
  { id: "decision_engine", label: "Decision Engine", steps: ["decision_engine"] },
  { id: "audit", label: "Audit & Recovery", steps: ["audit"] },
];

interface Props {
  claimId: number;
  userId: string;
  claimObject: string;
  userClaim: string;
  imageCount: number;
  imagePaths: string;
  savedResult?: OutputRow;
  onResult: (claimId: number, result: OutputRow) => void;
  onStepUpdate: (stepId: string, status: StepStatus, isRunning: boolean) => void;
  onRunStart: () => void;
  onRunComplete: (durationMs: number) => void;
}

export default function PipelineRunner({
  claimId,
  userId,
  claimObject,
  userClaim,
  imageCount,
  imagePaths,
  savedResult,
  onResult,
  onStepUpdate,
  onRunStart,
  onRunComplete,
}: Props) {
  const [steps, setSteps] = useState<Record<string, StepStatus>>({});
  const [result, setResult] = useState<OutputRow | null>(savedResult ?? null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPipeline, setShowPipeline] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const startTimeRef = useRef(0);

  const risk = estimateRisk({
    id: claimId,
    user_id: userId,
    claim_object: claimObject as "car" | "laptop" | "package",
    user_claim: userClaim,
    image_count: imageCount,
    image_paths: imagePaths,
  });

  const images = useMemo(() => imageNames(imagePaths, imageCount), [imagePaths, imageCount]);

  const handleEvent = useCallback(
    (event: PipelineEvent) => {
      if (event.type === "step_start") {
        setSteps((prev) => ({ ...prev, [event.step]: "running" }));
        onStepUpdate(event.step, "running", true);
      } else if (event.type === "step_complete") {
        setSteps((prev) => ({ ...prev, [event.step]: "complete" }));
        onStepUpdate(event.step, "complete", true);
      } else if (event.type === "step_skipped") {
        setSteps((prev) => ({ ...prev, [event.step]: "skipped" }));
        onStepUpdate(event.step, "skipped", true);
      } else if (event.type === "pipeline_complete") {
        setResult(event.output);
        onResult(claimId, event.output);
        setIsRunning(false);
        onRunComplete(Date.now() - startTimeRef.current);
      } else if (event.type === "error") {
        setError(event.message);
        setIsRunning(false);
        onRunComplete(Date.now() - startTimeRef.current);
      }
    },
    [claimId, onResult, onRunComplete, onStepUpdate]
  );

  const runPipeline = useCallback(() => {
    if (cleanupRef.current) cleanupRef.current();
    setSteps({});
    setResult(null);
    setError(null);
    setIsRunning(true);
    setShowPipeline(false);
    startTimeRef.current = Date.now();
    onRunStart();

    cleanupRef.current = streamPipeline(
      claimId,
      handleEvent,
      () => setIsRunning(false),
      () => {
        setError("Unable to connect to the analysis service.");
        setIsRunning(false);
      }
    );
  }, [claimId, handleEvent, onRunStart]);

  return (
    <aside className="flex h-full flex-col overflow-y-auto border-l border-slate-800/90 bg-[#0B1220]">
      <div className="border-b border-slate-800/90 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300/80">Selected Claim</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">Review details</h2>
      </div>

      <div className="space-y-5 p-6">
        <section className="rounded-2xl border border-slate-700/60 bg-[#111827] p-5 shadow-xl shadow-black/10">
          <div className="grid grid-cols-2 gap-4">
            <Detail label="Object" value={formatField(claimObject)} />
            <Detail label="Images" value={String(imageCount)} />
            <Detail label="Claim" value={summarizeClaim({ user_claim: userClaim, claim_object: claimObject })} wide />
            <Detail label="History" value={result ? statusLabel(result.claim_status) : risk.label} wide />
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-200">Image evidence</p>
            <p className="text-xs text-slate-500">{imageCount} submitted</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {images.map((name, index) => (
              <div
                key={`${name}-${index}`}
                className="group aspect-[4/3] overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900 shadow-lg shadow-black/10"
              >
                <div className="flex h-full flex-col justify-between bg-[radial-gradient(circle_at_30%_20%,rgba(34,211,238,0.16),transparent_36%),linear-gradient(135deg,#172033,#0f172a)] p-3">
                  <span className="w-fit rounded-full bg-black/25 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-300">
                    img{index + 1}
                  </span>
                  <span className="truncate text-xs font-medium text-slate-400">{name}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <button
          type="button"
          onClick={runPipeline}
          disabled={isRunning}
          className={`flex h-12 w-full items-center justify-center rounded-2xl border text-sm font-bold transition ${
            isRunning
              ? "border-slate-700 bg-slate-800 text-slate-500"
              : "border-cyan-300/35 bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-950/30 hover:-translate-y-0.5 hover:bg-cyan-300"
          }`}
        >
          {isRunning ? "Running analysis..." : result ? "Run Analysis Again" : "Run Analysis"}
        </button>

        {error && (
          <div className="rounded-2xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {result ? (
          <ResultCard result={result} />
        ) : (
          <section className="rounded-2xl border border-slate-700/50 bg-[#111827] p-5">
            <p className="text-sm font-semibold text-slate-200">Claim context</p>
            <p className="mt-3 line-clamp-4 text-sm leading-6 text-slate-400">{cleanClaimText(userClaim)}</p>
          </section>
        )}

        <section className="rounded-2xl border border-slate-700/50 bg-[#111827]">
          <button
            type="button"
            onClick={() => setShowPipeline((value) => !value)}
            className="flex w-full items-center justify-between p-5 text-left"
          >
            <span>
              <span className="block text-sm font-semibold text-slate-200">View Agent Pipeline</span>
              <span className="mt-1 block text-xs text-slate-500">Technical trace is hidden until needed.</span>
            </span>
            <span className="grid h-8 w-8 place-items-center rounded-full border border-slate-700 text-slate-400">
              {showPipeline ? "−" : "+"}
            </span>
          </button>

          {showPipeline && <PipelineTimeline steps={steps} isRunning={isRunning} />}
        </section>
      </div>
    </aside>
  );
}

function Detail({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? "col-span-2" : ""}>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold leading-6 text-slate-100">{value}</p>
    </div>
  );
}

function ResultCard({ result }: { result: OutputRow }) {
  return (
    <section className="rounded-2xl border border-slate-700/55 bg-[#111827] p-5 shadow-xl shadow-black/10">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-200">Analysis Result</p>
        <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${statusTone(result.claim_status)}`}>
          {statusLabel(result.claim_status)}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-4">
        <Detail label="Issue" value={formatField(result.issue_type, "Damage")} />
        <Detail label="Part" value={formatField(result.object_part, "Claimed area")} />
        <Detail label="Severity" value={formatField(result.severity, "Needs review")} />
        <Detail label="Supporting Images" value={supportingImages(result)} />
      </div>

      <div className="mt-5 rounded-2xl border border-slate-700/45 bg-slate-950/35 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Evidence Summary</p>
        <p className="mt-2 text-sm leading-6 text-slate-300">{evidenceSummary(result)}</p>
      </div>
    </section>
  );
}

function PipelineTimeline({ steps, isRunning }: { steps: Record<string, StepStatus>; isRunning: boolean }) {
  return (
    <div className="border-t border-slate-800/80 px-5 pb-5">
      <div className="mt-1">
        {TIMELINE.map((item, index) => {
          const status = resolveTimelineStatus(item.steps, steps, isRunning);
          return (
            <div key={item.id} className="relative flex gap-3 py-3">
              {index < TIMELINE.length - 1 && (
                <span className="absolute left-[11px] top-8 h-[calc(100%-1rem)] w-px bg-slate-700/70" />
              )}
              <span className={`relative z-10 grid h-6 w-6 place-items-center rounded-full border text-xs font-bold ${timelineDot(status)}`}>
                {status === "running" ? "•" : status === "complete" ? "✓" : ""}
              </span>
              <div className="pt-0.5">
                <p className={`text-sm font-semibold ${status === "complete" ? "text-slate-100" : status === "running" ? "text-cyan-200" : "text-slate-500"}`}>
                  {item.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function resolveTimelineStatus(ids: string[], steps: Record<string, StepStatus>, isRunning: boolean): StepStatus {
  if (ids.some((id) => steps[id] === "running")) return "running";
  if (ids.every((id) => steps[id] === "complete" || steps[id] === "skipped")) return "complete";
  if (isRunning && ids.some((id) => steps[id])) return "running";
  return "pending";
}

function timelineDot(status: StepStatus): string {
  if (status === "complete") return "border-emerald-400/30 bg-emerald-500/15 text-emerald-300";
  if (status === "running") return "border-cyan-400/40 bg-cyan-500/15 text-cyan-300 animate-pulse";
  return "border-slate-700 bg-slate-900 text-slate-600";
}
