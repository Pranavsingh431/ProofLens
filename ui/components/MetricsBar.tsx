"use client";

import { useMemo } from "react";
import type { ClaimSummary } from "@/types";

interface Props {
  claims: ClaimSummary[];
  loading: boolean;
}

interface MetricDef {
  icon:     string;
  label:    string;
  getValue: (claims: ClaimSummary[]) => string;
  color:    string;
  bgColor:  string;
}

const METRICS: MetricDef[] = [
  {
    icon: "◈", label: "Total Claims",
    getValue: (c) => String(c.length),
    color: "text-blue-400", bgColor: "bg-blue-500/10 border-blue-500/20",
  },
  {
    icon: "🚗", label: "Cars",
    getValue: (c) => String(c.filter((x) => x.claim_object === "car").length),
    color: "text-sky-400", bgColor: "bg-sky-500/10 border-sky-500/20",
  },
  {
    icon: "💻", label: "Laptops",
    getValue: (c) => String(c.filter((x) => x.claim_object === "laptop").length),
    color: "text-violet-400", bgColor: "bg-violet-500/10 border-violet-500/20",
  },
  {
    icon: "📦", label: "Packages",
    getValue: (c) => String(c.filter((x) => x.claim_object === "package").length),
    color: "text-orange-400", bgColor: "bg-orange-500/10 border-orange-500/20",
  },
  {
    icon: "⚙", label: "Active Agents",
    getValue: () => "10",
    color: "text-emerald-400", bgColor: "bg-emerald-500/10 border-emerald-500/20",
  },
  {
    icon: "🖼", label: "Avg Images",
    getValue: (c) => c.length === 0 ? "—"
      : (c.reduce((sum, x) => sum + x.image_count, 0) / c.length).toFixed(1),
    color: "text-cyan-400", bgColor: "bg-cyan-500/10 border-cyan-500/20",
  },
  {
    icon: "⚡", label: "Pipeline Steps",
    getValue: () => "10",
    color: "text-amber-400", bgColor: "bg-amber-500/10 border-amber-500/20",
  },
];

function SkeletonMetric() {
  return (
    <div className="flex-1 min-w-0 py-3 px-4 rounded-xl bg-slate-800/40 border border-slate-700/40 space-y-2">
      <div className="skeleton h-3 w-16 rounded" />
      <div className="skeleton h-6 w-10 rounded" />
      <div className="skeleton h-2 w-12 rounded" />
    </div>
  );
}

export default function MetricsBar({ claims, loading }: Props) {
  const values = useMemo(() => METRICS.map((m) => m.getValue(claims)), [claims]);

  return (
    <div className="shrink-0 border-b border-slate-800 bg-[rgb(2_8_23)]">
      <div className="flex items-stretch gap-px">
        {loading
          ? METRICS.map((_, i) => (
              <div key={i} className="flex-1 p-3">
                <SkeletonMetric />
              </div>
            ))
          : METRICS.map((metric, i) => (
              <div
                key={metric.label}
                className={`group flex-1 min-w-0 flex flex-col gap-1 py-3 px-4
                  border-r border-slate-800 last:border-r-0
                  hover:bg-slate-800/30 transition-colors cursor-default`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm ${metric.color}`}>{metric.icon}</span>
                  <span className={`text-[9px] font-semibold uppercase tracking-widest
                    px-1.5 py-0.5 rounded-full border ${metric.bgColor} ${metric.color}`}>
                    live
                  </span>
                </div>
                <p className="text-xl font-bold text-white tracking-tight leading-none">
                  {values[i]}
                </p>
                <p className="text-[11px] text-slate-500 leading-none">{metric.label}</p>
              </div>
            ))
        }
      </div>
    </div>
  );
}
