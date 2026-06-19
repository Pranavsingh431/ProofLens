"use client";

export default function JudgePanel({ loading }: { loading: boolean }) {
  if (loading) {
    return (
      <div className="flex flex-col gap-4 p-6">
        {[80, 60, 90, 50, 70].map((w, i) => (
          <div key={i} className={`skeleton h-4 rounded`} style={{ width: `${w}%` }} />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 p-5 animate-fade-in">

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-800/60 to-slate-900/40 p-5 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 pointer-events-none" />
        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <span className="text-white text-xs font-bold">PL</span>
            </div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              System Architecture
            </span>
          </div>
          <h2 className="text-lg font-bold text-white leading-tight mb-1.5">
            10-Component Multi-Agent Pipeline
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Deterministic decision engine backed by Gemini 2.5 Flash vision,
            with autonomous audit & recovery for claim verification.
          </p>
        </div>
      </div>

      {/* ── Agent pipeline ────────────────────────────────────────── */}
      <div className="space-y-2">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest px-1">
          Agent Pipeline
        </p>
        {AGENTS.map((agent) => (
          <AgentRow key={agent.id} agent={agent} />
        ))}
      </div>

      {/* ── Key architectural decisions ────────────────────────────── */}
      <div className="space-y-2">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest px-1">
          Key Design Decisions
        </p>
        <div className="grid grid-cols-1 gap-2">
          {DECISIONS.map((d) => (
            <div
              key={d.title}
              className="rounded-xl border border-slate-700/40 bg-slate-800/30 px-4 py-3
                flex items-start gap-3"
            >
              <span className="text-base shrink-0">{d.icon}</span>
              <div>
                <p className="text-xs font-semibold text-slate-300 leading-none">{d.title}</p>
                <p className="text-[11px] text-slate-500 leading-relaxed mt-0.5">{d.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA ───────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 px-4 py-3 flex items-center gap-3">
        <span className="text-blue-400 text-lg">←</span>
        <p className="text-sm text-slate-400">
          <span className="text-slate-300 font-medium">Select any claim</span> from the panel
          to run the live pipeline and watch all 10 agents execute in real time.
        </p>
      </div>
    </div>
  );
}

interface AgentDef {
  id: string;
  layer: string;
  name: string;
  desc: string;
  type: "llm" | "sys" | "cv";
  icon: string;
}

const TYPE_CONFIG = {
  llm: { label: "LLM",  bg: "bg-blue-500/10 text-blue-400 border-blue-500/25" },
  sys: { label: "SYS",  bg: "bg-slate-700/60 text-slate-400 border-slate-600/40" },
  cv:  { label: "CV",   bg: "bg-cyan-500/10 text-cyan-400 border-cyan-500/25" },
};

const AGENTS: AgentDef[] = [
  { id: "l1",      layer: "Layer 1",  name: "Signal Detector",       desc: "Prompt injection, threats, language detection",          type: "sys", icon: "🔍" },
  { id: "a1",      layer: "Agent 1",  name: "Hybrid Claim Parser",   desc: "Regex fast-path + Gemini LLM fallback",                  type: "llm", icon: "🧩" },
  { id: "a2",      layer: "Agent 2",  name: "Evidence Requirement",  desc: "Minimum evidence lookup from rules CSV",                 type: "sys", icon: "📋" },
  { id: "cg",      layer: "Guard",    name: "OpenCV Pre-check",      desc: "Reject corrupt/blurry images before VLM call",           type: "cv",  icon: "🖼️" },
  { id: "a34",     layer: "Agents 3+4", name: "Vision + Quality",   desc: "Gemini 2.5 Flash per image (parallel asyncio.gather)",   type: "llm", icon: "👁️" },
  { id: "a5",      layer: "Agent 5",  name: "Cross-image Fusion",    desc: "Deterministic aggregation — evidence_coverage_score",    type: "sys", icon: "🔀" },
  { id: "a5b",     layer: "Agent 5b", name: "Object-Part Validator", desc: "Rejects impossible part↔object combos → unknown",        type: "sys", icon: "✅" },
  { id: "a6",      layer: "Agent 6",  name: "History Risk",          desc: "User history flags — never overrides visual evidence",   type: "sys", icon: "🗂️" },
  { id: "a7",      layer: "Agent 7",  name: "Decision Engine",       desc: "Pure deterministic rules — zero LLM calls",              type: "sys", icon: "⚖️" },
  { id: "a8",      layer: "Agent 8",  name: "Audit & Recovery",      desc: "7 named rules, targeted re-run of affected agents",      type: "sys", icon: "🛡️" },
];

const DECISIONS = [
  { icon: "🎯", title: "VLM answers 'what is visible?' — never 'is the claim valid?'",     desc: "All verdict logic is deterministic rules in Agent 7. Eliminates hallucinated decisions." },
  { icon: "💸", title: "20–30% API call savings via OpenCV pre-checks",                    desc: "Corrupt/blurry images are rejected before reaching Gemini. Zero wasted tokens." },
  { icon: "⚡", title: "Agents 3+4 run in parallel per image",                             desc: "asyncio.gather for vision + quality. Minimises latency without exceeding rate limits." },
  { icon: "🛡️", title: "Audit agent re-runs individual modules, not the full pipeline",    desc: "Targeted recovery — cheaper and faster than restarting all 10 components." },
];

function AgentRow({ agent }: { agent: AgentDef }) {
  const tc = TYPE_CONFIG[agent.type];
  return (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-slate-700/30
      bg-slate-800/25 hover:bg-slate-800/40 hover:border-slate-700/60 transition-all">
      <span className="text-sm shrink-0 w-5 text-center">{agent.icon}</span>
      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 ${tc.bg}`}>
        {tc.label}
      </span>
      <span className="text-[10px] text-slate-600 font-mono w-16 shrink-0">{agent.layer}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-300 leading-none">{agent.name}</p>
        <p className="text-[10px] text-slate-600 leading-tight mt-0.5 truncate">{agent.desc}</p>
      </div>
    </div>
  );
}
