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
  { id: "all",     label: "All",      icon: "◈" },
  { id: "car",     label: "Cars",     icon: "🚗" },
  { id: "laptop",  label: "Laptops",  icon: "💻" },
  { id: "package", label: "Packages", icon: "📦" },
];

const STATUSES = [
  { id: "all",                    label: "Any status" },
  { id: "supported",              label: "Supported" },
  { id: "contradicted",           label: "Contradicted" },
  { id: "not_enough_information", label: "Insufficient" },
];

export default function FilterBar({
  filter, onFilterChange,
  search, onSearchChange,
  statusFilter, onStatusFilterChange,
  claims,
}: Props) {
  const getCounts = (id: string) =>
    id === "all" ? claims.length : claims.filter((c) => c.claim_object === id).length;

  return (
    <div className="shrink-0 flex items-center gap-3 px-4 py-3 border-b border-slate-800 bg-[rgb(2_8_23)/80]">

      {/* Object filter chips */}
      <div className="flex items-center gap-1.5">
        {TYPES.map((type) => {
          const count = getCounts(type.id);
          const active = filter === type.id;
          return (
            <button
              key={type.id}
              onClick={() => onFilterChange(type.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                transition-all duration-200 border
                ${active
                  ? "bg-blue-500/15 border-blue-500/40 text-blue-300 shadow-sm shadow-blue-500/10"
                  : "bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-slate-600 hover:text-slate-300"
                }`}
            >
              <span>{type.icon}</span>
              <span>{type.label}</span>
              <span className={`text-[10px] px-1 rounded-full transition-colors
                ${active ? "bg-blue-500/20 text-blue-400" : "bg-slate-700 text-slate-500"}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Separator */}
      <div className="h-6 w-px bg-slate-800" />

      {/* Search */}
      <div className="relative flex-1 min-w-0 max-w-xs">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs">⌕</span>
        <input
          type="text"
          placeholder="Search user ID or claim…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-slate-800/60 border border-slate-700/60 rounded-lg
            pl-7 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600
            focus:outline-none focus:border-blue-500/50 focus:bg-slate-800
            transition-all"
        />
      </div>

      {/* Status filter */}
      <select
        value={statusFilter}
        onChange={(e) => onStatusFilterChange(e.target.value)}
        className="bg-slate-800/60 border border-slate-700/60 rounded-lg px-2.5 py-1.5
          text-xs text-slate-300 focus:outline-none focus:border-blue-500/50
          transition-all cursor-pointer"
      >
        {STATUSES.map((s) => (
          <option key={s.id} value={s.id} className="bg-slate-900">
            {s.label}
          </option>
        ))}
      </select>

      {/* Spacer + count */}
      <div className="ml-auto text-xs text-slate-600 shrink-0">
        {claims.filter((c) => {
          const matchType = filter === "all" || c.claim_object === filter;
          const matchSearch = !search ||
            c.user_id.toLowerCase().includes(search.toLowerCase()) ||
            c.user_claim.toLowerCase().includes(search.toLowerCase());
          return matchType && matchSearch;
        }).length} / {claims.length}
      </div>
    </div>
  );
}
