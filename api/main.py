"""
ProofLens FastAPI backend.

Serves the claim list and streams pipeline execution events via SSE.

Run from repo root:
    uvicorn api.main:app --reload --port 8000
"""

import asyncio
import json
import os
import sys
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────
# Ensure the repo root (ProofLens/) is on sys.path so `code.*` imports work.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Load API key from code/.env (falls back to OS env on Render/prod)
_env_path = os.path.join(REPO_ROOT, "code", ".env")
load_dotenv(_env_path)

# ── Import pipeline modules after path is set ─────────────────────────
from code.core.loader import DataLoader  # noqa: E402

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(title="ProofLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tightened to Vercel domain in prod via env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton loader (loaded once at startup)
_loader: DataLoader | None = None
_claims: list[dict] | None = None


def _get_data() -> tuple[DataLoader, list[dict]]:
    global _loader, _claims
    if _loader is None:
        _loader = DataLoader()
        _claims = list(_loader.claims)
    return _loader, _claims


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "prooflens-api"}


@app.get("/api/claims")
async def list_claims():
    """Return lightweight summary of all claims in claims.csv."""
    _, claims = _get_data()
    result = []
    for i, row in enumerate(claims):
        img_paths = row.get("image_paths", "")
        image_count = len([p for p in img_paths.split(";") if p.strip()]) if img_paths else 0
        result.append({
            "id": i,
            "user_id": row.get("user_id", ""),
            "claim_object": row.get("claim_object", ""),
            "user_claim": row.get("user_claim", "")[:300],
            "image_count": image_count,
            "image_paths": img_paths,
        })
    return result


@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: int):
    """Return a single claim row by index."""
    _, claims = _get_data()
    if claim_id < 0 or claim_id >= len(claims):
        return {"error": "Invalid claim ID"}
    return {"id": claim_id, **claims[claim_id]}


@app.get("/api/claims/{claim_id}/run")
async def run_claim(claim_id: int, request: Request):
    """
    Stream pipeline execution events as Server-Sent Events.

    Each event is a JSON object with at minimum:
        type: "step_start" | "step_complete" | "step_skipped" |
              "pipeline_complete" | "error"
        step: step identifier string (for step_* events)
    """
    loader, claims = _get_data()
    if claim_id < 0 or claim_id >= len(claims):
        async def err_gen():
            yield f'data: {json.dumps({"type": "error", "message": "Invalid claim ID"})}\n\n'
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    row = claims[claim_id]
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def pipeline_task():
        try:
            from api.pipeline_runner import run_pipeline_with_events
            await run_pipeline_with_events(row, loader, queue.put)
        except Exception as exc:
            await queue.put({
                "type": "error",
                "message": str(exc),
                "trace": traceback.format_exc(),
            })
        finally:
            await queue.put(None)  # sentinel → end of stream

    task = asyncio.create_task(pipeline_task())

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
