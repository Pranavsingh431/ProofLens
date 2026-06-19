"use client";

interface Props {
  isRunning: boolean;
  activeStepId: string | null;
  totalRuns: number;
  lastRunMs: number | null;
  claimCount: number;
}

const STEP_LABELS: Record<string, string> = {
  signal_detection:      "Signal Detection",
  claim_parser:          "Claim Parser",
  evidence_requirement:  "Evidence Rules",
  precheck:              "Pre-check",
  vision_quality:        "Vision Analysis",
  fusion:                "Fusion",
  object_part_validator: "Validator",
  history_risk:          "Risk Assessment",
  decision_engine:       "Decision",
  audit:                 "Audit",
};

export default function Header({ isRunning, activeStepId, totalRuns, lastRunMs, claimCount }: Props) {
  return (
    <header className="shrink-0 h-16 border-b border-slate-800 bg-[rgb(2_8_23)] relative overflow-hidden">
      {/* Subtle gradient top accent */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />

      <div className="h-full flex items-center px-5 gap-6">

        {/* ── Logo ──────────────────────────────────────────── */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/25">
            <span className="text-white text-sm font-bold">PL</span>
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-none tracking-tight">ProofLens</h1>
            <p className="text-[10px] text-slate-500 leading-none mt-0.5 whitespace-nowrap">
              Multi-Agent Visual Evidence Verification
            </p>
          </div>
        </div>

        {/* ── Divider ───────────────────────────────────────── */}
        <div className="h-8 w-px bg-slate-800" />

        {/* ── Pipeline status ───────────────────────────────── */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center w-2 h-2">
            {isRunning && (
              <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75 animate-ping" />
            )}
            <span
              className={`relative inline-flex w-2 h-2 rounded-full transition-colors duration-300 ${
                isRunning ? "bg-blue-400" : "bg-emerald-400"
              }`}
            />
          </div>
          <div>
            <p className={`text-xs font-medium leading-none transition-colors ${
              isRunning ? "text-blue-300" : "text-emerald-300"
            }`}>
              {isRunning ? "Pipeline running" : "Pipeline ready"}
            </p>
            {isRunning && activeStepId && (
              <p className="text-[10px] text-slate-500 leading-none mt-0.5">
                {STEP_LABELS[activeStepId] ?? activeStepId}
              </p>
            )}
          </div>
        </div>

        {/* ── Model badge ───────────────────────────────────── */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <span className="text-[10px] text-purple-400">✦</span>
          <span className="text-[11px] font-medium text-purple-300">Gemini 2.5 Flash</span>
        </div>

        {/* ── Spacer ────────────────────────────────────────── */}
        <div className="flex-1" />

        {/* ── Quick stats ───────────────────────────────────── */}
        <div className="hidden lg:flex items-center gap-5">
          {[
            { label: "Claims",  value: String(claimCount) },
            { label: "Agents",  value: "10" },
            { label: "Runs",    value: String(totalRuns) },
            ...(lastRunMs !== null
              ? [{ label: "Last run", value: lastRunMs < 1000 ? `${lastRunMs}ms` : `${(lastRunMs/1000).toFixed(1)}s` }]
              : []
            ),
          ].map(({ label, value }) => (
            <div key={label} className="text-right">
              <p className="text-sm font-semibold text-white leading-none">{value}</p>
              <p className="text-[10px] text-slate-500 leading-none mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* ── Divider ───────────────────────────────────────── */}
        <div className="h-8 w-px bg-slate-800" />

        {/* ── Tech stack pill ───────────────────────────────── */}
        <div className="hidden xl:flex items-center gap-1.5 text-[10px] text-slate-600 divide-x divide-slate-700">
          {["FastAPI", "Next.js 16", "OpenRouter"].map((t) => (
            <span key={t} className="px-2 first:pl-0 last:pr-0">{t}</span>
          ))}
        </div>
      </div>
    </header>
  );
}
