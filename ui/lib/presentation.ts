import type { ClaimSummary, OutputRow } from "@/types";

export type DecisionStatus = "supported" | "contradicted" | "not_enough_information";

const ISSUE_WORDS = [
  "dent",
  "scratch",
  "crack",
  "shatter",
  "broken",
  "missing",
  "torn",
  "crushed",
  "water",
  "stain",
  "damage",
  "damaged",
];

const PART_WORDS = [
  "front bumper",
  "rear bumper",
  "bumper",
  "door",
  "hood",
  "windshield",
  "mirror",
  "headlight",
  "screen",
  "keyboard",
  "trackpad",
  "hinge",
  "lid",
  "corner",
  "box",
  "seal",
  "label",
  "package",
];

export function cleanClaimText(text: string): string {
  return text
    .split("|")
    .map((line) => line.trim().replace(/^(customer|agent|support):\s*/i, ""))
    .filter(Boolean)
    .join(" ");
}

export function summarizeClaim(claim: ClaimSummary | { user_claim: string; claim_object?: string }): string {
  const clean = cleanClaimText(claim.user_claim).replace(/\s+/g, " ").trim();
  const lower = clean.toLowerCase();
  const part = PART_WORDS.find((word) => lower.includes(word));
  const issue = ISSUE_WORDS.find((word) => lower.includes(word));

  if (part && issue) return `${toTitleCase(part)} ${normalizeIssueWord(issue)} reported`;
  if (issue) return `${normalizeIssueWord(issue)} reported`;
  if (part) return `${toTitleCase(part)} claim`;

  const firstSentence = clean.split(/[.!?]/)[0]?.trim();
  return firstSentence ? truncate(firstSentence, 74) : "Visual damage claim";
}

export function estimateRisk(claim: ClaimSummary): { label: string; confidence: number } {
  const lower = claim.user_claim.toLowerCase();
  const hasReviewSignal =
    lower.includes("escalate") ||
    lower.includes("approve") ||
    lower.includes("skip") ||
    lower.includes("ignore") ||
    lower.includes("not sure");

  if (hasReviewSignal) return { label: "Needs Review", confidence: 78 };
  if (claim.image_count >= 2) return { label: "Low Risk", confidence: 94 };
  return { label: "Medium Risk", confidence: 86 };
}

export function statusLabel(status?: string): string {
  if (status === "supported") return "SUPPORTED";
  if (status === "contradicted") return "CONTRADICTED";
  if (status === "not_enough_information") return "NEEDS REVIEW";
  return "PENDING";
}

export function statusTone(status?: string): string {
  if (status === "supported") return "text-emerald-300 bg-emerald-500/10 border-emerald-400/25";
  if (status === "contradicted") return "text-red-300 bg-red-500/10 border-red-400/25";
  if (status === "not_enough_information") return "text-amber-300 bg-amber-500/10 border-amber-400/25";
  return "text-slate-300 bg-slate-700/40 border-slate-600/40";
}

export function formatField(value?: string | boolean | null, fallback = "Pending review"): string {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (!value) return fallback;
  const text = String(value);
  if (text === "unknown" || text === "none") return fallback;
  return toTitleCase(text.replace(/_/g, " "));
}

export function supportingImages(row: OutputRow): string {
  const ids = row.supporting_image_ids
    ?.split(/[;,]/)
    .map((id) => id.trim())
    .filter((id) => id && id !== "none");
  return ids?.length ? ids.join(", ") : "Review image set";
}

export function evidenceSummary(row: OutputRow): string {
  if (row.claim_status === "supported") {
    return `Damage is visible on ${formatField(row.object_part, "the claimed part").toLowerCase()} in the submitted images.`;
  }
  if (row.claim_status === "contradicted") {
    return "The submitted images show the relevant area, but the reported damage is not visible.";
  }

  const reason = row.claim_status_justification || row.evidence_standard_met_reason;
  return sanitizeReason(reason) || "The images do not provide enough visual evidence to make a confident decision.";
}

export function sanitizeReason(reason: string): string {
  return reason
    .replace(/\s*\(coverage=[^)]+\)/gi, "")
    .replace(/\bunknown claim\b/gi, "claim")
    .replace(/_/g, " ")
    .trim();
}

export function imageNames(raw: string, count: number): string[] {
  const fromPaths = raw
    .split(";")
    .map((path) => path.trim().split("/").pop()?.replace(/\.[^.]+$/, ""))
    .filter(Boolean) as string[];

  if (fromPaths.length) return fromPaths;
  return Array.from({ length: count }, (_, i) => `img${i + 1}`);
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return `${text.slice(0, length - 1).trim()}...`;
}

export function toTitleCase(text: string): string {
  return text.replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

function normalizeIssueWord(issue: string): string {
  if (issue === "damaged") return "Damage";
  if (issue === "shatter") return "Shatter";
  return toTitleCase(issue);
}
