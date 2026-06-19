"use client";

import { useCallback, useEffect, useState } from "react";
import type { ClaimSummary, OutputRow, StepStatus } from "@/types";
import { fetchClaims } from "@/lib/api";
import { DEMO_CLAIMS } from "@/lib/demoData";
import ClaimsList from "@/components/ClaimsList";
import FilterBar from "@/components/FilterBar";
import PipelineRunner from "@/components/PipelineRunner";

type View = "dashboard" | "claims" | "architecture" | "evaluation";

const NAV: { id: View; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "claims", label: "Claims" },
  { id: "architecture", label: "Architecture" },
  { id: "evaluation", label: "Evaluation" },
];

export default function HomePage() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [activeView, setActiveView] = useState<View>("dashboard");

  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [results, setResults] = useState<Record<number, OutputRow>>({});

  const [activeStepId, setActiveStepId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [totalRuns, setTotalRuns] = useState(0);
  const [lastRunMs, setLastRunMs] = useState<number | null>(null);

  useEffect(() => {
    fetchClaims()
      .then((data) => {
        setClaims(data);
        setSelectedId(data[0]?.id ?? null);
      })
      .catch(() => {
        setClaims(DEMO_CLAIMS);
        setSelectedId(DEMO_CLAIMS[0]?.id ?? null);
        setFetchError(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const selected = selectedId !== null ? claims.find((claim) => claim.id === selectedId) ?? null : null;

  const handleStepUpdate = useCallback((stepId: string, status: StepStatus, running: boolean) => {
    setActiveStepId(running ? stepId : null);
    setIsRunning(status === "running" || running);
  }, []);

  const handleRunComplete = useCallback((durationMs: number) => {
    setIsRunning(false);
    setActiveStepId(null);
    setTotalRuns((n) => n + 1);
    setLastRunMs(durationMs);
  }, []);

  const handleRunStart = useCallback(() => {
    setActiveStepId(null);
    setIsRunning(true);
  }, []);

  const handleResult = useCallback((claimId: number, result: OutputRow) => {
    setResults((prev) => ({ ...prev, [claimId]: result }));
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-[#0B1220] text-slate-100">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        claimCount={claims.length}
        totalRuns={totalRuns}
        lastRunMs={lastRunMs}
        isRunning={isRunning}
        activeStepId={activeStepId}
      />

      {activeView === "architecture" ? (
        <ArchitecturePage />
      ) : activeView === "evaluation" ? (
        <EvaluationPage />
      ) : (
        <main className="grid min-w-0 flex-1 grid-cols-[minmax(420px,0.95fr)_minmax(420px,1.05fr)] overflow-hidden">
          <section className="flex min-w-0 flex-col overflow-hidden border-r border-slate-800/90 bg-[#0B1220]">
            <FilterBar
              filter={filter}
              onFilterChange={setFilter}
              search={search}
              onSearchChange={setSearch}
              statusFilter={statusFilter}
              onStatusFilterChange={setStatusFilter}
              claims={claims}
            />
            <div className="min-h-0 flex-1 overflow-y-auto">
              {fetchError ? (
                <ErrorState message={fetchError} />
              ) : (
                <ClaimsList
                  claims={claims}
                  loading={loading}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  filter={filter}
                  search={search}
                  statusFilter={statusFilter}
                  results={results}
                />
              )}
            </div>
          </section>

          {selected ? (
            <PipelineRunner
              key={selected.id}
              claimId={selected.id}
              userId={selected.user_id}
              claimObject={selected.claim_object}
              userClaim={selected.user_claim}
              imageCount={selected.image_count}
              imagePaths={selected.image_paths}
              savedResult={results[selected.id]}
              onResult={handleResult}
              onStepUpdate={handleStepUpdate}
              onRunStart={handleRunStart}
              onRunComplete={handleRunComplete}
            />
          ) : (
            <EmptyDetail loading={loading} />
          )}
        </main>
      )}
    </div>
  );
}

function Sidebar({
  activeView,
  setActiveView,
  claimCount,
  totalRuns,
  lastRunMs,
  isRunning,
}: {
  activeView: View;
  setActiveView: (view: View) => void;
  claimCount: number;
  totalRuns: number;
  lastRunMs: number | null;
  isRunning: boolean;
  activeStepId: string | null;
}) {
  return (
    <aside className="flex w-[280px] shrink-0 flex-col border-r border-slate-800/90 bg-[#080F1D] px-5 py-6">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-400 text-sm font-black text-slate-950 shadow-lg shadow-cyan-950/40">
          PL
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-white">ProofLens</h1>
          <p className="mt-0.5 text-xs leading-4 text-slate-500">Visual Damage Claim Verification</p>
        </div>
      </div>

      <nav className="mt-10 space-y-1">
        {NAV.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setActiveView(item.id)}
            className={`flex h-11 w-full items-center rounded-xl px-3 text-sm font-semibold transition ${
              activeView === item.id
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-500 hover:bg-slate-900/80 hover:text-slate-200"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="mt-8 rounded-2xl border border-slate-800 bg-[#111827] p-4">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Claims</span>
          <span className="text-sm font-semibold text-slate-100">{claimCount}</span>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-slate-500">Analyses</span>
          <span className="text-sm font-semibold text-slate-100">{totalRuns}</span>
        </div>
        {lastRunMs !== null && (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-slate-500">Last run</span>
            <span className="text-sm font-semibold text-slate-100">
              {lastRunMs < 1000 ? `${lastRunMs}ms` : `${(lastRunMs / 1000).toFixed(1)}s`}
            </span>
          </div>
        )}
      </div>

      <div className="mt-auto space-y-3">
        <div className="rounded-2xl border border-blue-400/20 bg-blue-500/10 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-200">Gemini 2.5 Flash</p>
          <p className="mt-1 text-xs text-slate-500">Vision reasoning via OpenRouter</p>
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3">
          <span className={`h-2.5 w-2.5 rounded-full ${isRunning ? "bg-cyan-300 animate-pulse" : "bg-emerald-300"}`} />
          <span className="text-sm font-semibold text-emerald-200">
            {isRunning ? "Pipeline Running" : "Pipeline Ready"}
          </span>
        </div>
      </div>
    </aside>
  );
}

function ArchitecturePage() {
  const stages = [
    "Claim Parser",
    "Evidence Requirements",
    "Vision Analysis",
    "Quality Analysis",
    "Cross Image Fusion",
    "Decision Engine",
    "Audit & Recovery",
  ];

  return (
    <main className="min-w-0 flex-1 overflow-y-auto bg-[#0B1220] p-8">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300/80">Architecture</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">Evidence-first claim verification</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          ProofLens separates visual evidence extraction from claim decisions, so the model reports what it sees and deterministic rules decide the claim.
        </p>

        <div className="mt-10 max-w-2xl">
          {stages.map((stage, index) => (
            <div key={stage}>
              <div className="flex min-h-20 items-center justify-between rounded-2xl border border-slate-700/60 bg-[#111827] px-6 py-5 shadow-xl shadow-black/10">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Step {index + 1}</p>
                  <p className="mt-1 text-lg font-semibold text-white">{stage}</p>
                </div>
                <span className="grid h-9 w-9 place-items-center rounded-full border border-cyan-400/25 bg-cyan-400/10 text-cyan-200">✓</span>
              </div>
              {index < stages.length - 1 && (
                <div className="flex h-9 items-center pl-8">
                  <span className="h-full w-px bg-gradient-to-b from-cyan-400/35 to-slate-700" />
                  <span className="ml-3 text-lg text-cyan-300/70">↓</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

function EvaluationPage() {
  const metrics = [
    { label: "Accuracy", value: "35.0%" },
    { label: "Precision", value: "25.2%" },
    { label: "Recall", value: "35.0%" },
    { label: "F1", value: "25.4%" },
  ];
  const matrix = [
    ["Contradicted", "0", "1", "3"],
    ["Needs Review", "0", "2", "1"],
    ["Supported", "1", "7", "5"],
  ];

  return (
    <main className="min-w-0 flex-1 overflow-y-auto bg-[#0B1220] p-8">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300/80">Evaluation</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">Sample-set performance</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          Metrics are shown from the generated evaluation report for the 20-row labeled sample.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-slate-700/60 bg-[#111827] p-5 shadow-xl shadow-black/10">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{metric.label}</p>
              <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{metric.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-8 rounded-2xl border border-slate-700/60 bg-[#111827] p-6 shadow-xl shadow-black/10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-white">Confusion Matrix</p>
              <p className="mt-1 text-sm text-slate-500">Actual vs predicted claim status</p>
            </div>
          </div>
          <div className="mt-6 overflow-x-auto rounded-2xl border border-slate-700/60">
            <div className="min-w-[620px]">
              <div className="grid grid-cols-4 bg-slate-950/40 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                <div className="p-4">Actual / Predicted</div>
                <div className="p-4">Contradicted</div>
                <div className="p-4">Needs Review</div>
                <div className="p-4">Supported</div>
              </div>
              {matrix.map((row) => (
                <div key={row[0]} className="grid grid-cols-4 border-t border-slate-700/60 text-sm text-slate-300">
                  {row.map((cell, index) => (
                    <div key={`${row[0]}-${index}`} className={`p-4 ${index === 0 ? "font-semibold text-slate-100" : ""}`}>
                      {cell}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function EmptyDetail({ loading }: { loading: boolean }) {
  return (
    <aside className="flex h-full flex-col items-center justify-center border-l border-slate-800/90 bg-[#0B1220] p-8 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-slate-700 bg-[#111827] text-slate-500">
        ⌕
      </div>
      <p className="mt-4 text-sm font-semibold text-slate-200">{loading ? "Loading claims" : "Select a claim"}</p>
      <p className="mt-2 max-w-xs text-sm leading-6 text-slate-500">
        Choose a claim from the browser to inspect its evidence and run analysis.
      </p>
    </aside>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex h-80 flex-col items-center justify-center gap-3 p-8 text-center">
      <div className="grid h-11 w-11 place-items-center rounded-2xl border border-red-400/25 bg-red-500/10 text-red-200">
        !
      </div>
      <p className="text-sm font-semibold text-slate-200">Backend unavailable</p>
      <p className="max-w-sm text-xs leading-5 text-slate-500">{message}</p>
    </div>
  );
}
