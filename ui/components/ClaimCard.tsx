"use client";

import { useState } from "react";
import type { ClaimSummary } from "@/types";

interface Props {
  claim: ClaimSummary;
  isSelected: boolean;
  onSelect: () => void;
}

const OBJECT_CONFIG: Record<string, { icon: string; badge: string; bg: string }> = {
  car:     { icon: "🚗", badge: "bg-sky-500/10 text-sky-300 border-sky-500/25",     bg: "hover:border-sky-500/20" },
  laptop:  { icon: "💻", badge: "bg-violet-500/10 text-violet-300 border-violet-500/25", bg: "hover:border-violet-500/20" },
  package: { icon: "📦", badge: "bg-orange-500/10 text-orange-300 border-orange-500/25", bg: "hover:border-orange-500/20" },
};

export default function ClaimCard({ claim, isSelected, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);
  const obj = OBJECT_CONFIG[claim.claim_object] ?? OBJECT_CONFIG.car;

  // Extract first meaningful line from claim text
  const claimLines = claim.user_claim
    .split("|")
    .map((l) => l.trim())
    .filter((l) => l.toLowerCase().startsWith("customer:"));
  const firstCustomerMsg = claimLines[0]?.replace(/^customer:\s*/i, "").trim() ?? claim.user_claim;

  return (
    <div
      onClick={onSelect}
      className={`group relative rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden
        ${isSelected
          ? "border-blue-500/50 bg-blue-500/5 shadow-md shadow-blue-500/10"
          : `border-slate-700/50 bg-slate-800/40 hover:bg-slate-800/60 ${obj.bg} hover:shadow-md hover:shadow-black/20 hover:-translate-y-px`
        }`}
    >
      {/* Selected accent bar */}
      {isSelected && (
        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-400 to-cyan-400" />
      )}

      <div className="p-3.5">
        {/* Header row */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs font-mono text-slate-500 shrink-0">{claim.user_id}</span>
            <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${obj.badge}`}>
              {obj.icon} {claim.claim_object}
            </span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {[...Array(Math.min(claim.image_count, 3))].map((_, i) => (
              <div key={i} className="w-3.5 h-3.5 rounded bg-slate-700 border border-slate-600
                flex items-center justify-center">
                <span className="text-[7px] text-slate-500">🖼</span>
              </div>
            ))}
            {claim.image_count > 3 && (
              <span className="text-[10px] text-slate-600">+{claim.image_count - 3}</span>
            )}
          </div>
        </div>

        {/* Claim preview */}
        <p className={`text-xs text-slate-300 leading-relaxed transition-all ${
          expanded ? "" : "line-clamp-2"
        }`}>
          {firstCustomerMsg}
        </p>

        {/* Expand control */}
        {claim.user_claim.length > 120 && (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded((s) => !s); }}
            className="mt-2 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
          >
            {expanded ? "Show less ▲" : "Show more ▼"}
          </button>
        )}

        {/* Expanded: full conversation */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-slate-700/50 text-[11px] text-slate-400 leading-relaxed
            space-y-1 max-h-40 overflow-y-auto">
            {claim.user_claim.split("|").map((line, i) => {
              const trimmed = line.trim();
              if (!trimmed) return null;
              const isCustomer = trimmed.toLowerCase().startsWith("customer:");
              const isAgent = trimmed.toLowerCase().startsWith("agent:") ||
                              trimmed.toLowerCase().startsWith("support:");
              return (
                <p key={i} className={isCustomer ? "text-slate-300" : isAgent ? "text-slate-500" : "text-slate-400"}>
                  {trimmed}
                </p>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3.5 pb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-600">
            {claim.image_count} image{claim.image_count !== 1 ? "s" : ""}
          </span>
        </div>
        <span className={`text-[10px] font-medium transition-colors ${
          isSelected ? "text-blue-400" : "text-slate-600 group-hover:text-slate-400"
        }`}>
          {isSelected ? "Selected ✓" : "Click to run →"}
        </span>
      </div>
    </div>
  );
}
