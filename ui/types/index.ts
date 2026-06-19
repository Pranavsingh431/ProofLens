// Shared TypeScript types for ProofLens UI

export type ClaimObject = "car" | "laptop" | "package";

export interface ClaimSummary {
  id: number;
  user_id: string;
  claim_object: ClaimObject;
  user_claim: string;
  image_count: number;
  image_paths: string;
}

export type StepStatus = "pending" | "running" | "complete" | "skipped" | "error";

export interface PipelineStepDef {
  id: string;
  label: string;
  description: string;
  icon: string;
  layer?: string;
}

export interface PipelineStep extends PipelineStepDef {
  status: StepStatus;
  data?: Record<string, unknown>;
  duration_ms?: number;
}

// ── SSE event union ──────────────────────────────────────────────────
export type PipelineEvent =
  | { type: "step_start"; step: string }
  | { type: "step_complete"; step: string; data: Record<string, unknown>; duration_ms: number }
  | { type: "step_skipped"; step: string; reason: string }
  | { type: "pipeline_complete"; output: OutputRow }
  | { type: "error"; message: string; trace?: string };

// ── Output row (14 columns) ──────────────────────────────────────────
export interface OutputRow {
  user_id: string;
  image_paths: string;
  user_claim: string;
  claim_object: string;
  evidence_standard_met: string | boolean;
  evidence_standard_met_reason: string;
  risk_flags: string;
  issue_type: string;
  object_part: string;
  claim_status: "supported" | "contradicted" | "not_enough_information";
  claim_status_justification: string;
  supporting_image_ids: string;
  valid_image: string | boolean;
  severity: string;
}
