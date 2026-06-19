// Static pipeline step definitions (order matters — it's the display order)
import type { PipelineStepDef } from "@/types";

export const PIPELINE_STEPS: PipelineStepDef[] = [
  {
    id: "signal_detection",
    label: "Signal Detector",
    description: "Prompt injection · threats · language detection",
    icon: "🔍",
    layer: "Layer 1",
  },
  {
    id: "claim_parser",
    label: "Claim Parser",
    description: "Regex fast-path + Gemini LLM fallback",
    icon: "🧩",
    layer: "Agent 1",
  },
  {
    id: "evidence_requirement",
    label: "Evidence Requirement",
    description: "Minimum visual evidence lookup",
    icon: "📋",
    layer: "Agent 2",
  },
  {
    id: "precheck",
    label: "OpenCV Pre-check",
    description: "Cost-aware routing — skip corrupt/blurry images",
    icon: "🖼️",
    layer: "Cost Guard",
  },
  {
    id: "vision_quality",
    label: "Vision + Quality",
    description: "Gemini 2.5 Flash per image (parallel)",
    icon: "👁️",
    layer: "Agents 3+4",
  },
  {
    id: "fusion",
    label: "Cross-image Fusion",
    description: "Deterministic aggregation across all images",
    icon: "🔀",
    layer: "Agent 5",
  },
  {
    id: "object_part_validator",
    label: "Object-Part Validator",
    description: "Rejects impossible part↔object combinations",
    icon: "✅",
    layer: "Agent 5b",
  },
  {
    id: "history_risk",
    label: "History Risk",
    description: "User claim history — flags only, never overrides",
    icon: "🗂️",
    layer: "Agent 6",
  },
  {
    id: "decision_engine",
    label: "Decision Engine",
    description: "Pure rules — zero LLM",
    icon: "⚖️",
    layer: "Agent 7",
  },
  {
    id: "audit",
    label: "Audit & Recovery",
    description: "7 consistency rules + targeted re-run",
    icon: "🛡️",
    layer: "Agent 8",
  },
];
