# ProofLens

<p align="center">
  <a href="https://github.com/Pranavsingh431/ProofLens/blob/main/output.csv">
    <img src="https://img.shields.io/badge/predictions-44%20rows-4CAF50?style=flat&logo=databricks&logoColor=white" />
  </a>
  <a href="https://github.com/Pranavsingh431/ProofLens/blob/main/code/evaluation/evaluation_report.md">
    <img src="https://img.shields.io/badge/evaluation-report-0077B5?style=flat&logo=readthedocs&logoColor=white" />
  </a>
  <img src="https://img.shields.io/badge/agents-10%20components-7C3AED?style=flat&logo=probot&logoColor=white" />
  <img src="https://img.shields.io/badge/vision-Gemini%202.5%20Flash-EA4335?style=flat&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/tests-140%20passing-22C55E?style=flat&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM%20decisions-zero-FF6B00?style=flat&logo=dependabot&logoColor=white" />
  <a href="https://proof-lens-zlpm.vercel.app">
    <img src="https://img.shields.io/badge/live%20UI-Vercel-000000?style=flat&logo=vercel&logoColor=white" />
  </a>
  <a href="https://linkedin.com/in/pranav-singh-8868a1283">
    <img src="https://img.shields.io/badge/LinkedIn-Pranav%20Singh-0077B5?style=flat&logo=linkedin&logoColor=white" />
  </a>
</p>

**Visual damage claim verification — HackerRank Orchestrate June 2026**

ProofLens decides whether submitted photos *support*, *contradict*, or provide *not enough information* for a reported damage claim. It processes cars, laptops, and packages through a 10-component multi-agent pipeline that separates image understanding from verdict logic — preventing the hallucinated decisions that plague single-model approaches.

---

## How it works

Each claim passes through a strict sequence of deterministic and vision stages. The key constraint: no model ever outputs a verdict. Models only describe what they see. A pure-rules engine makes every decision.

```
claims.csv row
      │
      ▼
┌─────────────────────────────────────────────┐
│  Layer 1 — Deterministic pre-processing     │
│                                             │
│  Signal detector   →  injection / threat /  │
│                        language flags       │
│  Taxonomy normalizer  →  VLM vocab → schema │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
           Agent 1 — Hybrid claim parser
           Regex fast path for simple English;
           Gemini 2.5 Flash fallback for
           multilingual, multi-part, or
           ambiguous claims
                       │
                       ▼
           Agent 2 — Evidence requirement lookup
           Reads evidence_requirements.csv;
           sets the bar before any image is seen
                       │
             ┌─────────┴─────────┐
             │   Per image (parallel)   │
             ▼                   ▼
        Agent 3             Agent 4
    Vision evidence      Image quality
    "What is visible?"   "Is this usable?"
    Gemini 2.5 Flash     Gemini 2.5 Flash
    OpenCV gate: corrupt / extreme-blur →
    skip both agents entirely
             └─────────┬─────────┘
                       │
                       ▼
           Agent 5 — Deterministic fusion
           Aggregates findings across all images;
           computes evidence_coverage_score
                       │
                       ▼
           Agent 5b — Object-part validator
           Catches impossible combos
           e.g. (car, keyboard) → unknown
                       │
                       ▼
           Agent 6 — History risk
           Reads user_history.csv;
           adds risk_flags only —
           never touches claim_status
                       │
                       ▼
           Agent 7 — Decision engine (zero LLM)
           evidence not met   → not_enough_information
           part + damage match → supported
           part visible, no match → contradicted
                       │
                       ▼
           Agent 8 — Audit & recovery
           7 named consistency rules;
           targeted agent re-run on failure —
           never restarts the full pipeline
                       │
                       ▼
           Layer 5 — CSV formatter
           14-column schema enforcement;
           allowed-value hard gate
                       │
                       ▼
              output.csv row
```

---

## Design decisions

| Decision | Why |
|---|---|
| VLM asks only "what is visible?" — never "is this claim valid?" | Keeps verdict logic inside the deterministic rule engine, eliminating hallucinated decisions |
| Agent 1 is a hybrid: regex fast path + LLM fallback | Simple English claims never reach Gemini, cutting ~50% of Agent 1 API calls |
| OpenCV pre-checks gate every VLM call | Corrupt, too-small, and extreme-blur images are rejected before Gemini is invoked, saving 20–30% of vision calls |
| Agent 5 (fusion) is pure Python, not an LLM | Aggregation is logic, not reasoning — deterministic, cheap, and trivially testable |
| Agent 6 (history risk) writes only `risk_flags` | User history adds context but cannot reverse clear visual evidence; matches the problem spec exactly |
| Agent 8 re-runs individual agents, not the pipeline | Targeted recovery is faster and cheaper than a full restart |
| Confidence score on every agent output | Audit agent triggers re-run when decision confidence falls below 0.65 |
| Temperature 0.1 on all LLM calls | Produces consistent, structured JSON; minimises output variance across runs |

---

## Repository layout

```
ProofLens/
├── context.md                     ← architecture log, updated after each phase
├── output.csv                     ← final predictions (44 rows, 14 columns)
├── dataset/
│   ├── claims.csv
│   ├── sample_claims.csv
│   ├── user_history.csv
│   ├── evidence_requirements.csv
│   └── images/
│       ├── sample/
│       └── test/
└── code/
    ├── main.py                    ← pipeline entry point
    ├── requirements.txt
    ├── .env.example
    ├── agents/
    │   ├── claim_parser.py        ← Agent 1: hybrid regex + Gemini
    │   ├── evidence_requirement.py← Agent 2: CSV lookup
    │   ├── vision_evidence.py     ← Agent 3: VLM per image
    │   ├── image_quality.py       ← Agent 4: VLM per image
    │   ├── cross_image_fusion.py  ← Agent 5: deterministic aggregation
    │   ├── object_part_validator.py← Agent 5b: schema guard
    │   ├── history_risk.py        ← Agent 6: risk flags only
    │   ├── decision_engine.py     ← Agent 7: pure rules
    │   ├── audit_recovery.py      ← Agent 8: consistency + targeted re-run
    │   └── csv_formatter.py       ← Layer 5
    ├── core/
    │   ├── config.py              ← constants, thresholds, allowed values
    │   ├── models.py              ← Pydantic schemas (confidence on every output)
    │   ├── loader.py
    │   ├── signal_detector.py     ← injection / threat / language detection
    │   ├── taxonomy.py            ← 59-entry VLM vocab → schema normaliser
    │   ├── openrouter.py          ← API wrapper with retry + semaphore
    │   └── precheck.py            ← OpenCV blur / brightness / corruption checks
    ├── tests/
    │   ├── test_core.py           49 tests
    │   ├── test_agent1.py         6 tests
    │   ├── test_agents_3_4.py     10 tests
    │   ├── test_agents_5_6.py     13 tests
    │   ├── test_agents_7_8.py     6 tests
    │   ├── test_pipeline_e2e.py   28 tests
    │   └── test_evaluation.py     28 tests
    └── evaluation/
        ├── main.py
        ├── metrics.py
        └── evaluation_report.md
```

---

## Setup

**Requirements:** Python 3.11+, an OpenRouter API key with access to `google/gemini-2.5-flash`

```bash
# Install dependencies
pip install -r code/requirements.txt

# Configure API key
cp code/.env.example code/.env
# Add OPENROUTER_API_KEY to code/.env
```

---

## Running

**Full pipeline** — reads `dataset/claims.csv`, writes `output.csv`:

```bash
python -m code.main
```

**Evaluation** — runs the pipeline against `sample_claims.csv` and writes `code/evaluation/evaluation_report.md`:

```bash
python -m code.evaluation.main --real       # requires images + API key
python -m code.evaluation.main --synthetic  # offline, reproducible baseline
```

**Tests** — 140 tests total, all passing:

```bash
PYTHONPATH=code python -m pytest code/tests/ -v
```

---

## Output schema

The 14 required output columns, in exact submission order:

| Column | Values |
|--------|--------|
| `user_id` | Claimant identifier |
| `image_paths` | Semicolon-separated input paths |
| `user_claim` | Raw conversation transcript |
| `claim_object` | `car` · `laptop` · `package` |
| `evidence_standard_met` | `true` · `false` |
| `evidence_standard_met_reason` | One-sentence explanation |
| `risk_flags` | Semicolon-separated flags, or `none` |
| `issue_type` | `dent` · `scratch` · `crack` · `glass_shatter` · `broken_part` · `missing_part` · `torn_packaging` · `crushed_packaging` · `water_damage` · `stain` · `none` · `unknown` |
| `object_part` | Object-specific part name, or `unknown` |
| `claim_status` | `supported` · `contradicted` · `not_enough_information` |
| `claim_status_justification` | Image-grounded explanation, references image IDs |
| `supporting_image_ids` | Semicolon-separated image IDs, or `none` |
| `valid_image` | `true` · `false` |
| `severity` | `none` · `low` · `medium` · `high` · `unknown` |

---

## Special signal handling

The pipeline handles four categories of adversarial or unusual input that appear in the test set. All are detected before any LLM call.

| Signal | Detection method | Handling |
|--------|-----------------|----------|
| Prompt injection in `user_claim` | `SignalDetector` regex, runs pre-LLM | Sets `text_instruction_present` risk flag; real claim still extracted normally |
| Multilingual claims (Hindi, Spanish, Chinese, mixed) | Language keyword scoring in `SignalDetector` | Routes Agent 1 to Gemini fallback; no special handling otherwise |
| Escalation threats ("will keep reopening", "escalate publicly") | Threat-pattern regex | Sets `manual_review_required` flag; verdict is never biased |
| Instructions embedded inside an image | Agents 3 + 4 vision analysis | Flagged as `text_instruction_present`; instruction content ignored for evidence |

---

## Cost and latency

| Metric | Sample — 20 rows | Full test — 44 rows |
|--------|-----------------|---------------------|
| Agent 1 LLM calls (fallback only) | ~5–10 | ~10–22 |
| Vision API calls (Agents 3 + 4, parallel) | ~30–40 | ~66–88 |
| Images skipped by OpenCV gate | ~20–30% | ~20–30% |
| Estimated cost at Gemini 2.5 Flash pricing | ~$0.009 | ~$0.020 |
| Estimated wall-clock runtime | 2–3 min | 5–7 min |

**Rate-limit strategy:** `asyncio.Semaphore(5)` caps concurrent OpenRouter requests. All calls retry up to 3 times with exponential backoff (2 s → 4 s → 8 s) on HTTP 429, 500, 502, and 503.

---

## Evaluation results

Results on `sample_claims.csv` in offline mode (images not available locally):

| Field | Accuracy | Note |
|-------|----------|------|
| `claim_status` | 0.15 | All rows default to `not_enough_information` without images |
| `issue_type` | 0.15 | Same — requires visual evidence |
| `object_part` | **0.75** | Agent 1 extracts the claimed part from text alone, regardless of images |
| `severity` | 0.15 | Defaults to `unknown` without visual input |
| `evidence_standard_met` | 0.15 | All `false` without images |
| `valid_image` | 0.15 | All `false` without images |

Full accuracy figures are produced in the HackerRank sandbox where `dataset/images/` is present and Gemini vision analysis runs against real images.

---

## Pipeline visualiser (UI)

An interactive web interface that streams each agent's output in real time as a claim is processed. Built with Next.js 16 and FastAPI, deployed on Vercel and Render.

Each pipeline step emits a Server-Sent Event on completion:

```json
{
  "type": "step_complete",
  "step": "claim_parser",
  "duration_ms": 1200,
  "data": {
    "claimed_issue": "dent",
    "claimed_part": "rear_bumper",
    "path": "llm_fallback"
  }
}
```

**Run locally:**

```bash
# Backend
pip install -r code/requirements.txt -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend
cd ui && cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install && npm run dev
```

**Deploy:**

| Service | Steps |
|---------|-------|
| **Render** (backend) | Connect repo → `render.yaml` is auto-detected → add `OPENROUTER_API_KEY` as a secret env var |
| **Vercel** (frontend) | Import repo → `vercel.json` sets `rootDirectory: ui` → add `NEXT_PUBLIC_API_URL` pointing to your Render URL → deploy |

---

## Submission

| File | Description |
|------|-------------|
| `output.csv` | Predictions for all 44 rows in `claims.csv` |
| `code.zip` | Full runnable solution including `evaluation/` folder |
| `code/evaluation/evaluation_report.md` | Per-field accuracy, strategy comparison, full operational analysis |
