// API client for ProofLens backend
import type { ClaimSummary, PipelineEvent } from "@/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export async function fetchClaims(): Promise<ClaimSummary[]> {
  const res = await fetch(`${API_URL}/api/claims`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch claims: ${res.status}`);
  return res.json();
}

export function streamPipeline(
  claimId: number,
  onEvent: (event: PipelineEvent) => void,
  onDone: () => void,
  onError: (err: Event) => void
): () => void {
  const es = new EventSource(`${API_URL}/api/claims/${claimId}/run`);

  es.onmessage = (ev) => {
    if (!ev.data || ev.data.startsWith(":")) return; // keepalive
    try {
      const parsed = JSON.parse(ev.data) as PipelineEvent;
      onEvent(parsed);
      if (parsed.type === "pipeline_complete" || parsed.type === "error") {
        es.close();
        onDone();
      }
    } catch {
      // ignore parse errors on malformed frames
    }
  };

  es.onerror = (err) => {
    es.close();
    onError(err);
    onDone();
  };

  return () => es.close(); // cleanup function
}
