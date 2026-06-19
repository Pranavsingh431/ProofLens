"use client";

import type { StepStatus } from "@/types";
import { PIPELINE_STEPS } from "@/lib/steps";

interface Props {
  stepStatuses: Record<string, StepStatus>;
  activeStepId: string | null;
  isRunning: boolean;
}

const TYPE_LABELS: Record<string, { label: string; color: string }> = {
  signal_detection:      { label: "L1",  color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
  claim_parser:          { label: "LLM", color: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
  evidence_requirement:  { label: "SYS", color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
  precheck:              { label: "CV",  color: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30" },
  vision_quality:        { label: "LLM", color: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
  fusion:                { label: "SYS", color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
  object_part_validator: { label: "SYS", color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
  history_risk:          { label: "SYS", color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
  decision_engine:       { label: "SYS", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
  audit:                 { label: "SYS", color: "bg-slate-600/60 text-slate-400 border-slate-500/40" },
};

function NodeDot({ status, isActive }: { status: StepStatus; isActive: boolean }) {
  if (isActive) {
    return (
      <div className="relative w-2.5 h-2.5 flex items-center justify-center">
        <span className="absolute w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping opacity-75" />
        <span className="relative w-2 h-2 rounded-full bg-blue-400" />
      </div>
    );
  }
  const colors: Record<StepStatus, string> = {
    pending:  "bg-slate-600",
    running:  "bg-blue-400 animate-pulse",
    complete: "bg-emerald-400",
    skipped:  "bg-slate-700",
    error:    "bg-red-400",
  };
  return <span className={`w-2 h-2 rounded-full ${colors[status]}`} />;
}

export default function PipelineArchViz({ stepStatuses, activeStepId }: Props) {
  return (
    <div className="shrink-0 border-b border-slate-800 bg-[rgb(2_8_23)/95] px-5 py-2.5">
      <div className="flex items-center gap-0">

        {PIPELINE_STEPS.map((step, i) => {
          const status = stepStatuses[step.id] ?? "pending";
          const isActive = activeStepId === step.id;
          const isComplete = status === "complete";
          const nextStatus = i < PIPELINE_STEPS.length - 1
            ? (stepStatuses[PIPELINE_STEPS[i + 1].id] ?? "pending")
            : "pending";
          const typeInfo = TYPE_LABELS[step.id];

          return (
            <div key={step.id} className="flex items-center flex-1 min-w-0">
              {/* Node */}
              <div
                className={`flex flex-col items-center gap-1 px-2 py-1.5 rounded-lg transition-all duration-300
                  ${isActive
                    ? "bg-blue-500/10 border border-blue-500/30 shadow-sm shadow-blue-500/20"
                    : isComplete
                      ? "bg-emerald-500/5 border border-emerald-500/20"
                      : "border border-transparent"
                  }`}
              >
                <div className="flex items-center gap-1.5">
                  <NodeDot status={status} isActive={isActive} />
                  <span className={`text-[10px] font-medium transition-colors whitespace-nowrap
                    ${isActive ? "text-blue-300" : isComplete ? "text-emerald-300" : "text-slate-500"}`}>
                    {step.icon} {step.label}
                  </span>
                  {typeInfo && (
                    <span className={`text-[8px] px-1 py-0.5 rounded border font-mono font-semibold ${typeInfo.color}`}>
                      {typeInfo.label}
                    </span>
                  )}
                </div>
              </div>

              {/* Connector */}
              {i < PIPELINE_STEPS.length - 1 && (
                <div className={`flex-1 h-px mx-0.5 transition-all duration-500
                  ${isComplete && nextStatus !== "pending"
                    ? "bg-gradient-to-r from-emerald-500/60 to-emerald-500/30"
                    : isComplete
                      ? "bg-gradient-to-r from-emerald-500/40 to-slate-700"
                      : "bg-slate-800"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
