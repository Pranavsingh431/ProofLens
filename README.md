# ProofLens — Visual Damage Claim Verification

A 10-component multi-agent pipeline that verifies damage claims by analysing submitted images, parsing the user conversation, checking user history, and applying a pure-rules decision engine to produce a final claim verdict.

Built for **HackerRank Orchestrate June 2026**.

---

## What it does

For each row in `dataset/claims.csv`, ProofLens produces one row in `output.csv` that answers:

> "Do the submitted images **support**, **contradict**, or provide **not enough information** for this damage claim?"

Object types handled: `car` | `laptop` | `package`

---

## Pipeline architecture

```
CSV row (claims.csv)
        │
┌───────────────────────────────────────────┐
│  LAYER 1 — Deterministic pre-processing   │
│  CSV loader → Signal detector             │
│           → Taxonomy normalizer           │
└───────────────┬───────────────────────────┘
                │
        AGENT 1 — Hybrid Claim Parser
        Regex fast path (simple English) +
        Gemini 2.5 Flash fallback (multilingual / complex / multi-part)
                │
        AGENT 2 — Evidence Requirement (deterministic)
        Looks up minimum visual evidence from evidence_requirements.csv
                │
        ┌───────┴────────┐
        │ PARALLEL/IMAGE │
   AGENT 3          AGENT 4
   Vision evidence  Image quality
   (Gemini per img) (Gemini per img)
   OpenCV pre-check gates both — invalid images skip VLM entirely
        └───────┬────────┘
                │
        AGENT 5 — Cross-image Fusion (deterministic)
        Aggregates findings, computes evidence_coverage_score
                │
        AGENT 5b — Object-Part Validator (deterministic)
        Rejects impossible part↔object combos → "unknown"
                │
        AGENT 6 — History Risk (deterministic)
        Adds user_history_risk flags — never overrides visual evidence
                │
        AGENT 7 — Decision Engine (pure rules, zero LLM)
        ├─ not evidence_met → not_enough_information
        ├─ part visible + damage matches → supported
        └─ part visible + damage mismatch → contradicted
                │
        AGENT 8 — Audit & Recovery
        7 named rules check consistency; re-runs affected agents on fail
                │
        LAYER 5 — CSV Formatter
        14-column schema enforcement + allowed-value validation
                │
        output.csv row
```

### Key design decisions

| Decision | Rationale |
|---|---|
| VLM only answers "what is visible?" | Keeps verdict logic in the deterministic rule engine; prevents hallucinated decisions |
| Agents 3+4 run in parallel via `asyncio.gather` | Minimises per-image latency |
| Agent 1 is hybrid: regex fast path + LLM fallback | Simple English claims never hit Gemini; saves ~50% of Agent 1 LLM calls |
| OpenCV pre-checks before every VLM call | Corrupt / extreme-blur / too-small images are rejected before reaching Gemini; saves ~20–30% API calls |
| Agent 5 (fusion) is deterministic, not an LLM | `target_part_visible = OR over valid images`; fast, cheap, testable |
| Agent 6 (history) affects only `risk_flags` | Never overrides clear visual evidence; matches problem spec exactly |
| Agent 8 (audit) re-runs individual agents only | Targeted recovery is faster and cheaper than a full pipeline restart |
| Confidence score on every agent output | Audit triggers re-run when confidence < 0.65 |
| Temperature 0.1 for all LLM calls | Consistent, structured JSON output |

---

## Repository structure

```
ProofLens/
├── README.md
├── context.md                 ← architecture, decisions, phase log
├── output.csv                 ← final predictions (44 rows, 14 columns)
├── dataset/
│   ├── claims.csv
│   ├── sample_claims.csv
│   ├── user_history.csv
│   ├── evidence_requirements.csv
│   └── images/sample/ + images/test/   ← provided in sandbox
└── code/
    ├── main.py                ← pipeline entry point
    ├── requirements.txt
    ├── .env.example
    ├── agents/
    │   ├── claim_parser.py        ← Agent 1
    │   ├── evidence_requirement.py← Agent 2
    │   ├── vision_evidence.py     ← Agent 3
    │   ├── image_quality.py       ← Agent 4
    │   ├── cross_image_fusion.py  ← Agent 5
    │   ├── object_part_validator.py ← Agent 5b
    │   ├── history_risk.py        ← Agent 6
    │   ├── decision_engine.py     ← Agent 7
    │   ├── audit_recovery.py      ← Agent 8
    │   └── csv_formatter.py       ← Layer 5
    ├── core/
    │   ├── config.py
    │   ├── models.py              ← all Pydantic schemas
    │   ├── loader.py
    │   ├── signal_detector.py
    │   ├── taxonomy.py
    │   ├── openrouter.py          ← API wrapper + retry
    │   └── precheck.py            ← OpenCV pre-checks
    ├── tests/
    │   ├── test_core.py           (49 tests)
    │   ├── test_agent1.py         (6 tests)
    │   ├── test_agents_3_4.py     (10 tests)
    │   ├── test_agents_5_6.py     (13 tests)
    │   ├── test_agents_7_8.py     (6 tests)
    │   ├── test_pipeline_e2e.py   (28 tests)
    │   └── test_evaluation.py     (28 tests)
    └── evaluation/
        ├── main.py
        ├── metrics.py
        └── evaluation_report.md
```

---

## Setup

### Requirements

- Python 3.11+
- An [OpenRouter](https://openrouter.ai/) API key with access to `google/gemini-2.5-flash`

### Install

```bash
pip install -r code/requirements.txt
```

### Configure

```bash
cp code/.env.example code/.env
# Edit code/.env and set your OPENROUTER_API_KEY
```

---

## Running

### Full pipeline (produces `output.csv`)

```bash
python -m code.main
```

Reads `dataset/claims.csv`, writes `output.csv` in the repository root.

### Evaluation (produces `code/evaluation/evaluation_report.md`)

```bash
# Real mode (requires image files + API key)
python -m code.evaluation.main --real

# Synthetic mode (offline, reproducible baseline)
python -m code.evaluation.main --synthetic
```

### Tests

```bash
PYTHONPATH=code python -m pytest code/tests/ -v
```

All 140 tests pass.

---

## Output schema

The 14 required columns, in order:

| Column | Description |
|--------|-------------|
| `user_id` | Claimant identifier |
| `image_paths` | Semicolon-separated input image paths |
| `user_claim` | Raw conversation transcript |
| `claim_object` | `car` / `laptop` / `package` |
| `evidence_standard_met` | `true` / `false` — image set sufficient for evaluation |
| `evidence_standard_met_reason` | Short explanation |
| `risk_flags` | Semicolon-separated flags, or `none` |
| `issue_type` | Detected damage type |
| `object_part` | Relevant object part |
| `claim_status` | `supported` / `contradicted` / `not_enough_information` |
| `claim_status_justification` | Image-grounded explanation |
| `supporting_image_ids` | Semicolon-separated image IDs, or `none` |
| `valid_image` | `true` / `false` — image set usable for automated review |
| `severity` | `none` / `low` / `medium` / `high` / `unknown` |

---

## Special signal handling

| Signal | Detection | Handling |
|--------|-----------|----------|
| Prompt injection in `user_claim` | `SignalDetector` (regex, pre-LLM) | Sets `text_instruction_present` flag; claim is parsed normally |
| Multilingual claims (hi / es / zh / mixed) | Language detection in `SignalDetector` | Routes to LLM fallback in Agent 1 |
| Escalation threats | Threat-language patterns in `SignalDetector` | Sets `manual_review_required` flag; never biases verdict |
| Note/instruction inside an image | Agent 3 + 4 vision analysis | Flagged; instruction content is ignored for decisions |
| Multi-part claims | Agent 1 LLM extraction | Both `claimed_part` and `secondary_part` extracted and evaluated |

---

## Cost and latency

| Metric | Sample (20 rows) | Full test (44 rows) |
|--------|-----------------|---------------------|
| LLM calls (Agent 1 fallback) | ~5–10 | ~10–22 |
| Vision API calls (Agents 3+4) | ~30–40 | ~66–88 |
| Cost-aware routing savings | ~20–30% | ~20–30% |
| Estimated cost (Gemini 2.5 Flash pricing) | ~$0.009 | ~$0.020 |
| Estimated runtime | ~2–3 min | ~5–7 min |

**Retry strategy:** 3 attempts with exponential backoff (2 s, 4 s, 8 s) for transient API errors (429, 500, 502, 503).

---

## Evaluation results (sample set, real pipeline mode)

| Field | Accuracy (without images) | Notes |
|-------|--------------------------|-------|
| `claim_status` | 0.1500 | All `not_enough_information` — images not present locally; full accuracy requires sandbox images |
| `issue_type` | 0.1500 | Same reason |
| `object_part` | **0.7500** | Agent 1 correctly extracts the claimed part from text alone |
| `severity` | 0.1500 | Defaults to `unknown` without visual evidence |
| `evidence_standard_met` | 0.1500 | All `false` without images |
| `valid_image` | 0.1500 | All `false` without images |

> In the HackerRank sandbox where `dataset/images/` is available, Gemini 2.5 Flash vision analysis runs for each image and the verdict accuracy improves substantially.

---

## UI — Pipeline Visualiser

An interactive web UI that lets you browse all 44 claims and watch each agent process a claim in real time via Server-Sent Events.

```
ui/ (Next.js 16, Tailwind)  →  Vercel
api/ (FastAPI, SSE)         →  Render
```

Each pipeline step emits a structured SSE event as it completes:

```json
{"type": "step_complete", "step": "claim_parser", "duration_ms": 1200,
 "data": {"claimed_issue": "dent", "claimed_part": "rear_bumper", "path": "llm_fallback"}}
```

### Run locally

**Backend (FastAPI)**

```bash
pip install -r code/requirements.txt -r api/requirements.txt
# ensure OPENROUTER_API_KEY is in code/.env
uvicorn api.main:app --reload --port 8000
```

**Frontend (Next.js)**

```bash
cd ui
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install && npm run dev   # → http://localhost:3000
```

### Deploy to Render + Vercel

**Render (backend)**
1. Create a new Web Service, connect `Pranavsingh431/ProofLens`
2. Render auto-detects `render.yaml` — no manual config needed
3. Add `OPENROUTER_API_KEY` as a secret environment variable
4. Note the service URL, e.g. `https://prooflens-api.onrender.com`

**Vercel (frontend)**
1. Import `Pranavsingh431/ProofLens` in the Vercel dashboard
2. `vercel.json` sets `rootDirectory: ui` automatically
3. Add env var `NEXT_PUBLIC_API_URL=https://prooflens-api.onrender.com`
4. Deploy — Vercel builds and publishes automatically

---

## Submission files

| File | Description |
|------|-------------|
| `output.csv` | Predictions for all 44 rows in `claims.csv` |
| `code.zip` | Full runnable solution |
| `code/evaluation/evaluation_report.md` | Evaluation report with metrics, strategy comparisons, operational analysis |
