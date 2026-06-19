"use client";

import type { ClaimSummary, OutputRow } from "@/types";
import ClaimCard from "./ClaimCard";

interface Props {
  claims: ClaimSummary[];
  loading: boolean;
  selectedId: number | null;
  onSelect: (id: number) => void;
  filter: string;
  search: string;
  statusFilter: string;
  results: Record<number, OutputRow>;
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-slate-700/45 bg-[#111827] p-4">
      <div className="flex items-center justify-between">
        <div className="skeleton h-3 w-20 rounded" />
        <div className="skeleton h-6 w-16 rounded-full" />
      </div>
      <div className="mt-5 space-y-3">
        <div className="skeleton h-4 w-4/5 rounded" />
        <div className="skeleton h-3 w-20 rounded" />
      </div>
      <div className="mt-5 flex items-center justify-between border-t border-slate-700/45 pt-3">
        <div className="skeleton h-6 w-24 rounded-full" />
        <div className="skeleton h-3 w-24 rounded" />
      </div>
    </div>
  );
}

export default function ClaimsList({
  claims,
  loading,
  selectedId,
  onSelect,
  filter,
  search,
  statusFilter,
  results,
}: Props) {
  const q = search.trim().toLowerCase();
  const filtered = claims.filter((claim) => {
    const result = results[claim.id];
    const matchType = filter === "all" || claim.claim_object === filter;
    const matchSearch =
      !q ||
      claim.user_id.toLowerCase().includes(q) ||
      claim.user_claim.toLowerCase().includes(q);
    const matchStatus =
      statusFilter === "all" ||
      (statusFilter === "needs_review"
        ? result?.claim_status === "not_enough_information" || !result
        : result?.claim_status === statusFilter);

    return matchType && matchSearch && matchStatus;
  });

  if (loading) {
    return (
      <div className="space-y-3 p-5">
        {Array.from({ length: 7 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 px-8 text-center">
        <div className="grid h-10 w-10 place-items-center rounded-2xl border border-slate-700 bg-slate-800 text-slate-500">
          <span className="text-lg">⌕</span>
        </div>
        <p className="text-sm font-semibold text-slate-300">No matching claims</p>
        <p className="max-w-xs text-xs leading-5 text-slate-500">
          Try a different object type, status, or user search.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-5">
      {filtered.map((claim) => (
        <ClaimCard
          key={claim.id}
          claim={claim}
          result={results[claim.id]}
          isSelected={selectedId === claim.id}
          onSelect={() => onSelect(claim.id)}
        />
      ))}
    </div>
  );
}
