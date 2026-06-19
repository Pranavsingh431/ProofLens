"use client";

import { useState, useEffect } from "react";
import type { ClaimSummary } from "@/types";
import { fetchClaims } from "@/lib/api";
import ClaimsList from "@/components/ClaimsList";
import PipelineRunner from "@/components/PipelineRunner";

export default function HomePage() {
  const [claims, setClaims]       = useState<ClaimSummary[]>([]);
  const [loading, setLoading]     = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [filter, setFilter]       = useState("all");
  const [search, setSearch]       = useState("");

  useEffect(() => {
    fetchClaims()
      .then(setClaims)
      .catch((err: Error) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const selected = selectedId !== null ? claims[selectedId] : null;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* ── Top nav ───────────────────────────────────────────────── */}
      <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔬</span>
          <div>
            <h1 className="text-lg font-bold text-white leading-none">ProofLens</h1>
            <p className="text-xs text-slate-400">Visual damage claim verification</p>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-6">
          {[
            { label: "10", sub: "agents" },
            { label: "44", sub: "claims" },
            { label: "3", sub: "object types" },
          ].map(({ label, sub }) => (
            <div key={sub} className="text-center">
              <p className="text-base font-bold text-blue-400 leading-none">{label}</p>
              <p className="text-[10px] text-slate-500">{sub}</p>
            </div>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse inline-block" />
          Pipeline ready
        </div>
      </header>

      {/* ── Main content ──────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — claims list */}
        <aside className="w-80 shrink-0 border-r border-slate-700 flex flex-col overflow-hidden bg-slate-900">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="animate-spin w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full" />
            </div>
          ) : fetchError ? (
            <div className="p-4 text-red-400 text-sm">
              <p className="font-semibold">Failed to load claims</p>
              <p className="text-xs mt-1 text-slate-400">{fetchError}</p>
              <p className="text-xs mt-2 text-slate-500">
                Make sure the backend is running at{" "}
                <code className="bg-slate-700 px-1 rounded">
                  {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                </code>
              </p>
            </div>
          ) : (
            <ClaimsList
              claims={claims}
              selectedId={selectedId}
              onSelect={setSelectedId}
              filter={filter}
              onFilterChange={setFilter}
              search={search}
              onSearchChange={setSearch}
            />
          )}
        </aside>

        {/* Right panel — pipeline visualization */}
        <main className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <PipelineRunner
              claimId={selected.id}
              userId={selected.user_id}
              claimObject={selected.claim_object}
              userClaim={selected.user_claim}
              imageCount={selected.image_count}
            />
          ) : (
            <EmptyState loading={loading} />
          )}
        </main>
      </div>
    </div>
  );
}

function EmptyState({ loading }: { loading: boolean }) {
  if (loading) return null;
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
      <span className="text-6xl opacity-30">🔬</span>
      <div>
        <h2 className="text-xl font-semibold text-slate-300">Select a claim to begin</h2>
        <p className="text-slate-500 text-sm mt-1 max-w-sm">
          Choose any of the 44 claims from the sidebar, then click{" "}
          <strong className="text-slate-300">Run Pipeline</strong> to watch all 10 agents
          process it in real time.
        </p>
      </div>

      {/* Architecture mini-diagram */}
      <div className="mt-4 bg-slate-800 rounded-xl border border-slate-700 p-5 max-w-lg text-left">
        <p className="text-xs font-semibold text-slate-400 mb-3 uppercase tracking-wider">
          Pipeline overview
        </p>
        {[
          ["🔍", "Layer 1",   "Signal Detector — prompt injection, language"],
          ["🧩", "Agent 1",   "Hybrid Claim Parser — regex + LLM fallback"],
          ["📋", "Agent 2",   "Evidence Requirement — minimum evidence lookup"],
          ["🖼️", "Cost Guard", "OpenCV Pre-check — skip corrupt/blurry images"],
          ["👁️", "Agents 3+4", "Vision + Quality — Gemini 2.5 Flash (parallel)"],
          ["🔀", "Agent 5",   "Cross-image Fusion — deterministic aggregation"],
          ["✅", "Agent 5b",  "Object-Part Validator — schema enforcement"],
          ["🗂️", "Agent 6",   "History Risk — flags only, never overrides"],
          ["⚖️", "Agent 7",   "Decision Engine — pure rules, zero LLM"],
          ["🛡️", "Agent 8",   "Audit & Recovery — 7 rules + targeted re-run"],
        ].map(([icon, layer, desc]) => (
          <div key={layer} className="flex items-start gap-2 py-1">
            <span className="text-sm w-5 shrink-0">{icon}</span>
            <span className="text-[11px] w-20 shrink-0 text-blue-400 font-mono">{layer}</span>
            <span className="text-xs text-slate-400">{desc}</span>
          </div>
        ))}
      </div>

      <p className="text-[11px] text-slate-600 max-w-sm">
        Note: vision results require images in{" "}
        <code className="bg-slate-800 px-1 rounded">dataset/images/</code>.
        Without them, the pipeline runs all text-based agents and gracefully
        returns <em>not_enough_information</em>.
      </p>
    </div>
  );
}
