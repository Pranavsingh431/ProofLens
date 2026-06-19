"use client";

import type { ClaimSummary } from "@/types";
import ClaimCard from "./ClaimCard";

interface Props {
  claims: ClaimSummary[];
  loading: boolean;
  selectedId: number | null;
  onSelect: (id: number) => void;
  filter: string;
  search: string;
  statusFilter: string;
}

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-slate-700/40 bg-slate-800/30 p-3.5 space-y-3">
      <div className="flex items-center gap-2">
        <div className="skeleton h-3 w-16 rounded" />
        <div className="skeleton h-4 w-14 rounded-full" />
      </div>
      <div className="skeleton h-3 w-full rounded" />
      <div className="skeleton h-3 w-4/5 rounded" />
      <div className="skeleton h-2.5 w-20 rounded mt-1" />
    </div>
  );
}

export default function ClaimsList({
  claims, loading, selectedId, onSelect,
  filter, search, statusFilter,
}: Props) {
  const filtered = claims.filter((c) => {
    const matchType   = filter === "all" || c.claim_object === filter;
    const matchSearch = !search ||
      c.user_id.toLowerCase().includes(search.toLowerCase()) ||
      c.user_claim.toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  if (loading) {
    return (
      <div className="p-4 grid grid-cols-2 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-2">
        <span className="text-2xl opacity-20">◈</span>
        <p className="text-slate-500 text-sm">No claims match your filters</p>
      </div>
    );
  }

  return (
    <div className="p-4 grid grid-cols-2 gap-3">
      {filtered.map((claim) => (
        <ClaimCard
          key={claim.id}
          claim={claim}
          isSelected={selectedId === claim.id}
          onSelect={() => onSelect(claim.id)}
        />
      ))}
    </div>
  );
}
