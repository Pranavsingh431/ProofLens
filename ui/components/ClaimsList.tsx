"use client";

import type { ClaimSummary } from "@/types";

interface Props {
  claims: ClaimSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  filter: string;
  onFilterChange: (f: string) => void;
  search: string;
  onSearchChange: (s: string) => void;
}

const OBJECT_ICONS: Record<string, string> = {
  car:     "🚗",
  laptop:  "💻",
  package: "📦",
};

const OBJECT_COLORS: Record<string, string> = {
  car:     "bg-blue-900/30 text-blue-300 border-blue-700/40",
  laptop:  "bg-purple-900/30 text-purple-300 border-purple-700/40",
  package: "bg-orange-900/30 text-orange-300 border-orange-700/40",
};

export default function ClaimsList({
  claims,
  selectedId,
  onSelect,
  filter,
  onFilterChange,
  search,
  onSearchChange,
}: Props) {
  const filtered = claims.filter((c) => {
    const matchesFilter = filter === "all" || c.claim_object === filter;
    const matchesSearch =
      !search ||
      c.user_id.toLowerCase().includes(search.toLowerCase()) ||
      c.user_claim.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-slate-700">
        <input
          type="text"
          placeholder="Search user or claim…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2
            placeholder-slate-400 border border-slate-600 focus:outline-none
            focus:border-blue-500 transition-colors"
        />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 p-2 border-b border-slate-700">
        {["all", "car", "laptop", "package"].map((f) => {
          const count =
            f === "all"
              ? claims.length
              : claims.filter((c) => c.claim_object === f).length;
          return (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`flex-1 text-xs font-medium py-1.5 px-1 rounded-md transition-colors
                ${filter === f
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                }`}
            >
              {OBJECT_ICONS[f] ?? "📋"} {f === "all" ? "All" : f} ({count})
            </button>
          );
        })}
      </div>

      {/* Claims list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="text-slate-500 text-sm text-center p-6">No claims found</p>
        ) : (
          <ul className="divide-y divide-slate-700/50">
            {filtered.map((claim) => (
              <li key={claim.id}>
                <button
                  onClick={() => onSelect(claim.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-slate-700/60 transition-colors
                    ${selectedId === claim.id ? "bg-slate-700 border-l-2 border-blue-500" : ""}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-slate-400 text-xs font-mono">{claim.user_id}</span>
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border
                        ${OBJECT_COLORS[claim.claim_object] ?? "bg-slate-700 text-slate-300 border-slate-600"}`}
                    >
                      {OBJECT_ICONS[claim.claim_object]} {claim.claim_object}
                    </span>
                    <span className="text-slate-600 text-[10px] ml-auto">
                      {claim.image_count}🖼
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs leading-snug line-clamp-2">
                    {claim.user_claim}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer count */}
      <div className="px-4 py-2 border-t border-slate-700 text-slate-500 text-xs text-center">
        {filtered.length} / {claims.length} claims
      </div>
    </div>
  );
}
