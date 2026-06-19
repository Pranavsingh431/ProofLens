"use client";

import type { ClaimSummary, OutputRow } from "@/types";
import { estimateRisk, statusLabel, statusTone, summarizeClaim } from "@/lib/presentation";

interface Props {
  claim: ClaimSummary;
  result?: OutputRow;
  isSelected: boolean;
  onSelect: () => void;
}

const OBJECT_BADGE: Record<string, string> = {
  car: "text-sky-300 bg-sky-500/10 border-sky-400/20",
  laptop: "text-cyan-300 bg-cyan-500/10 border-cyan-400/20",
  package: "text-blue-300 bg-blue-500/10 border-blue-400/20",
};

export default function ClaimCard({ claim, result, isSelected, onSelect }: Props) {
  const risk = estimateRisk(claim);
  const status = result?.claim_status;
  const footerLabel = result ? statusLabel(status) : risk.label;
  const confidence = result ? confidenceFromStatus(status) : risk.confidence;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`group w-full rounded-2xl border p-4 text-left transition-all duration-200 ${
        isSelected
          ? "border-cyan-400/45 bg-cyan-400/[0.07] shadow-lg shadow-cyan-950/35"
          : "border-slate-700/55 bg-[#111827] hover:-translate-y-0.5 hover:border-slate-500/70 hover:bg-slate-800/80"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="font-mono text-xs font-semibold text-slate-400">{claim.user_id}</p>
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${OBJECT_BADGE[claim.claim_object]}`}>
          {claim.claim_object}
        </span>
      </div>

      <div className="mt-4 space-y-2">
        <p className="text-sm font-semibold leading-6 text-slate-100">{summarizeClaim(claim)}</p>
        <p className="text-xs font-medium text-slate-500">
          {claim.image_count} image{claim.image_count === 1 ? "" : "s"}
        </p>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3 border-t border-slate-700/45 pt-3">
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] ${result ? statusTone(status) : "border-emerald-400/20 bg-emerald-500/10 text-emerald-300"}`}>
          {footerLabel}
        </span>
        <span className="text-xs font-semibold text-slate-300">{confidence}% confidence</span>
      </div>
    </button>
  );
}

function confidenceFromStatus(status?: string): number {
  if (status === "supported") return 94;
  if (status === "contradicted") return 88;
  if (status === "not_enough_information") return 72;
  return 84;
}
