"use client";

import type { ClaimSummary } from "@/types";

interface Props {
  filter: string;
  onFilterChange: (f: string) => void;
  search: string;
  onSearchChange: (s: string) => void;
  statusFilter: string;
  onStatusFilterChange: (s: string) => void;
  claims: ClaimSummary[];
}

const TYPES = [
  { id: "all", label: "All" },
  { id: "car", label: "Cars" },
  { id: "laptop", label: "Laptops" },
  { id: "package", label: "Packages" },
];

const STATUSES = [
  { id: "all", label: "All" },
  { id: "supported", label: "Supported" },
  { id: "contradicted", label: "Contradicted" },
  { id: "needs_review", label: "Needs Review" },
];

export default function FilterBar({
  filter,
  onFilterChange,
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  claims,
}: Props) {
  return (
    <div className="border-b border-slate-800/90 bg-[#0B1220]/95 p-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300/80">Claim Browser</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">Visual evidence queue</h1>
        </div>
        <div className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1.5 text-xs font-medium text-slate-400">
          {claims.length} claims
        </div>
      </div>

      <div className="mt-5">
        <label className="relative block">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm text-slate-500">⌕</span>
          <input
            type="text"
            placeholder="Search by user or claim..."
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            className="h-12 w-full rounded-2xl border border-slate-700/70 bg-[#111827] pl-10 pr-4 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-400/60 focus:ring-4 focus:ring-cyan-400/10"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {TYPES.map((type) => (
          <Chip
            key={type.id}
            label={type.label}
            active={filter === type.id}
            onClick={() => onFilterChange(type.id)}
          />
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {STATUSES.map((status) => (
          <Chip
            key={status.id}
            label={status.label}
            active={statusFilter === status.id}
            onClick={() => onStatusFilterChange(status.id)}
            subtle
          />
        ))}
      </div>
    </div>
  );
}

function Chip({
  label,
  active,
  onClick,
  subtle = false,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  subtle?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3.5 py-2 text-xs font-semibold transition ${
        active
          ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-200 shadow-sm shadow-cyan-950/40"
          : subtle
            ? "border-slate-700/70 bg-slate-900/45 text-slate-400 hover:border-slate-500 hover:text-slate-200"
            : "border-slate-700/70 bg-[#111827] text-slate-400 hover:border-slate-500 hover:text-slate-200"
      }`}
    >
      {label}
    </button>
  );
}
