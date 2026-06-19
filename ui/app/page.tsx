"use client";

import { useState, useEffect, useCallback } from "react";
import type { ClaimSummary, StepStatus } from "@/types";
import { fetchClaims } from "@/lib/api";
import Header from "@/components/Header";
import MetricsBar from "@/components/MetricsBar";
import PipelineArchViz from "@/components/PipelineArchViz";
import FilterBar from "@/components/FilterBar";
import ClaimsList from "@/components/ClaimsList";
import PipelineRunner from "@/components/PipelineRunner";
import JudgePanel from "@/components/JudgePanel";

export default function HomePage() {
  const [claims, setClaims]         = useState<ClaimSummary[]>([]);
  const [loading, setLoading]       = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Filters
  const [filter, setFilter]         = useState("all");
  const [search, setSearch]         = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Live pipeline state (lifted up for Header + ArchViz)
  const [activeStepId, setActiveStepId]   = useState<string | null>(null);
  const [isRunning, setIsRunning]         = useState(false);
  const [stepStatuses, setStepStatuses]   = useState<Record<string, StepStatus>>({});
  const [totalRuns, setTotalRuns]         = useState(0);
  const [lastRunMs, setLastRunMs]         = useState<number | null>(null);

  useEffect(() => {
    fetchClaims()
      .then(setClaims)
      .catch((err: Error) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleStepUpdate = useCallback(
    (stepId: string, status: StepStatus, running: boolean) => {
      setActiveStepId(running ? stepId : null);
      setIsRunning(running);
      setStepStatuses((prev) => ({ ...prev, [stepId]: status }));
    },
    []
  );

  const handleRunComplete = useCallback((durationMs: number) => {
    setIsRunning(false);
    setActiveStepId(null);
    setTotalRuns((n) => n + 1);
    setLastRunMs(durationMs);
  }, []);

  const handleRunStart = useCallback(() => {
    setStepStatuses({});
    setActiveStepId(null);
  }, []);

  const selected = selectedId !== null ? claims[selectedId] : null;

  return (
    <div className="flex flex-col h-screen bg-[rgb(2_8_23)] overflow-hidden">

      {/* ── Header ────────────────────────────────────────────────── */}
      <Header
        isRunning={isRunning}
        activeStepId={activeStepId}
        totalRuns={totalRuns}
        lastRunMs={lastRunMs}
        claimCount={claims.length}
      />

      {/* ── Metrics bar ───────────────────────────────────────────── */}
      <MetricsBar claims={claims} loading={loading} />

      {/* ── Pipeline architecture viz ────────────────────────────── */}
      <PipelineArchViz stepStatuses={stepStatuses} activeStepId={activeStepId} isRunning={isRunning} />

      {/* ── Main split content ───────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Left: filter + claims grid */}
        <div className="flex flex-col flex-1 min-w-0 border-r border-slate-800">
          <FilterBar
            filter={filter}
            onFilterChange={setFilter}
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
            claims={claims}
          />
          <div className="flex-1 overflow-y-auto">
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
              />
            )}
          </div>
        </div>

        {/* Right: pipeline runner or judge panel */}
        <div className="w-[46%] shrink-0 flex flex-col overflow-y-auto bg-[rgb(2_8_23)]">
          {selected ? (
            <PipelineRunner
              key={selected.id}
              claimId={selected.id}
              userId={selected.user_id}
              claimObject={selected.claim_object}
              userClaim={selected.user_claim}
              imageCount={selected.image_count}
              onStepUpdate={handleStepUpdate}
              onRunStart={handleRunStart}
              onRunComplete={handleRunComplete}
            />
          ) : (
            <JudgePanel loading={loading} />
          )}
        </div>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3 p-8">
      <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 text-lg">
        ⚠
      </div>
      <p className="text-slate-300 font-medium text-sm">Backend unreachable</p>
      <p className="text-slate-500 text-xs text-center max-w-xs">{message}</p>
      <code className="text-xs bg-slate-800 px-3 py-1.5 rounded-lg text-slate-400 border border-slate-700">
        uvicorn api.main:app --reload --port 8000
      </code>
    </div>
  );
}
