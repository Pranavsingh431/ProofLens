# Project context — HackerRank Orchestrate June 2026

## Challenge summary
Visual damage claim verification. For each row in `dataset/claims.csv`, produce
one row in `output.csv` that decides whether submitted images support, contradict,
or provide insufficient evidence for a reported damage claim.

Object types: **car**, **laptop**, **package**

## Repo
`interviewstreet/hackerrank-orchestrate-june26` (upstream)  
Your fork / own remote: point `origin` at your own GitHub repo for PRs.

---

## Architecture — 10-component multi-agent pipeline

```
Input row (claims.csv)
        │
┌───────────────────────────────────────┐
│ LAYER 1 — deterministic pre-processing│
│  CSV loader → Signal detector         │
│           → Taxonomy normalizer       │
└───────────────┬───────────────────────┘
                │
        AGENT 1 — Hybrid Claim Parser
        ├─ Regex/keyword parser (fast path)
        └─ LLM fallback (multilingual, complex)
        Extracts: claimed_issue, claimed_part,
        keywords, language, multi_part, confidence
        Handles: English / Hindi / Spanish / Chinese / mixed
        Ignores: prompt injection instructions in text
                │
        AGENT 2 — Evidence requirement (deterministic)
        Reads evidence_requirements.csv
        Returns: minimum_image_evidence for this object+issue
                │
        ┌───────┴────────┐
        │ PARALLEL/IMAGE │
        │                │
   AGENT 3          AGENT 4
   Vision evidence  Image quality
   (VLM per image)  (VLM per image)
   what is visible? blur/crop/manip?
   Returns confidence  Returns confidence
        │                │
        └───────┬────────┘
                │
        AGENT 5 — Cross-image fusion (DETERMINISTIC)
        Aggregates all findings across images
        Returns: target_part_visible, damage_consistent,
                 evidence_standard_met, supporting_image_ids,
                 evidence_coverage_score, confidence
                │
        AGENT 5b — Object-Part Validator (deterministic)
        Validates: object+part combinations are valid
        Auto-corrects impossible pairs → "unknown"
                │
        AGENT 6 — History risk (deterministic)
        Reads user_history.csv
        Returns: risk_flags ONLY — never affects claim_status
                │
        AGENT 7 — Decision engine (pure rules, zero LLM)
        if not evidence_met          → not_enough_information
        if part + damage match       → supported
        if part visible + no match   → contradicted
        Uses: evidence_coverage_score threshold
                │
        AGENT 8 — Audit & Recovery (orchestrator)
        Checks: issue_type↔claim, object_part↔claim,
                severity↔evidence, flags↔signals,
                vision_confidence thresholds
        On fail: re-runs ONLY the affected module
                │
        LAYER 5 — CSV formatter
        14 columns, exact schema, allowed-values enforcement
                │
        output.csv row
```

**Cost-aware routing:** OpenCV pre-checks (corrupt, extreme blur, dimensions) run before any VLM call. Failed pre-checks → `valid_image=false`, skip Gemini entirely. Saves ~20-30% API calls.

---

## Vision model
**Gemini 2.5 Flash** via **OpenRouter**  
`model: "google/gemini-2.5-flash"`  
Temperature: 0.1 | `response_format: json_object` | Retry: 3× exponential backoff

---

## Dataset facts (reverse-engineered)

| Fact | Value |
|------|-------|
| claims.csv rows | 44 |
| sample_claims.csv rows | 20 (labeled) |
| claim_object split (test) | 18 car / 13 laptop / 13 package |
| images per case | 1→13 cases, 2→24 cases, 3→7 cases |
| Users in both sample + test | 14 overlapping user IDs |

### Special signals in test set (found by data analysis)
| Signal | Count | Handling |
|--------|-------|----------|
| Prompt injection in user_claim | 6 | `text_instruction_present` flag; extract real claim anyway |
| Multilingual claims (hi/es/zh/mixed) | 10+ | Parse regardless of language |
| Escalation threats ("escalate publicly") | 2 | `manual_review_required` flag; never bias decision |
| Multi-part claims (two damaged parts) | 2 | Evaluate both claimed_part and secondary_part |
| Color-specific claims ("blue car") | 2 | Check vehicle color in image matches claim |
| Note/instruction inside image | 2 | `text_instruction_present` flag; ignore instruction |

---

## Schema — required output columns (exact order)

```
user_id, image_paths, user_claim, claim_object,
evidence_standard_met, evidence_standard_met_reason,
risk_flags, issue_type, object_part,
claim_status, claim_status_justification,
supporting_image_ids, valid_image, severity
```

### Allowed values

**claim_status:** `supported` | `contradicted` | `not_enough_information`

**issue_type:** `dent` | `scratch` | `crack` | `glass_shatter` | `broken_part` |
`missing_part` | `torn_packaging` | `crushed_packaging` | `water_damage` |
`stain` | `none` | `unknown`

**car object_part:** `front_bumper` | `rear_bumper` | `door` | `hood` | `windshield` |
`side_mirror` | `headlight` | `taillight` | `fender` | `quarter_panel` | `body` | `unknown`

**laptop object_part:** `screen` | `keyboard` | `trackpad` | `hinge` | `lid` |
`corner` | `port` | `base` | `body` | `unknown`

**package object_part:** `box` | `package_corner` | `package_side` | `seal` |
`label` | `contents` | `item` | `unknown`

**risk_flags:** `none` | `blurry_image` | `cropped_or_obstructed` | `low_light_or_glare` |
`wrong_angle` | `wrong_object` | `wrong_object_part` | `damage_not_visible` |
`claim_mismatch` | `possible_manipulation` | `non_original_image` |
`text_instruction_present` | `user_history_risk` | `manual_review_required`

**severity:** `none` | `low` | `medium` | `high` | `unknown`

---

## File structure

```
hackerrank-orchestrate-june26/
├── context.md                     ← THIS FILE
├── output.csv                     ← final predictions
├── dataset/                       ← provided, read-only
│   ├── claims.csv
│   ├── sample_claims.csv
│   ├── user_history.csv
│   ├── evidence_requirements.csv
│   └── images/sample/ + images/test/
└── code/
    ├── main.py                    ← pipeline entry point ✅ (full 10-component E2E)
    ├── requirements.txt
    ├── .env.example
    ├── agents/
    │   ├── claim_parser.py        ← Agent 1 ✅ (hybrid: regex + LLM)
    │   ├── evidence_requirement.py← Agent 2 ✅ (deterministic)
    │   ├── vision_evidence.py     ← Agent 3 ✅ (VLM + confidence)
    │   ├── image_quality.py       ← Agent 4 ✅ (VLM + OpenCV pre-check)
    │   ├── cross_image_fusion.py  ← Agent 5 ✅ (deterministic fusion)
    │   ├── object_part_validator.py ← Agent 5b ✅ (deterministic)
    │   ├── history_risk.py        ← Agent 6 ✅ (deterministic)
    │   ├── decision_engine.py     ← Agent 7 ✅ (pure rules, zero LLM)
    │   ├── audit_recovery.py      ← Agent 8 ✅ (7 named-function rules, targeted re-run)
    │   └── csv_formatter.py       ← Layer 5 ✅ (14-column schema enforcement + validation)
    ├── core/
    │   ├── config.py              ✅ Phase 1: paths, models, allowed-value sets, EVIDENCE_COVERAGE_THRESHOLD
    │   ├── models.py              ✅ Phase 1: 10 Pydantic schemas + confidence fields
    │   ├── loader.py              ✅ Phase 1: DataLoader, 4 CSVs, image path resolution, validate_image_paths
    │   ├── signal_detector.py     ✅ Phase 1+fix: SignalDetector class, 9 injection patterns, 5 threat patterns, mixed-language detection
    │   ├── taxonomy.py            ✅ Phase 1+fix: normalize_issue (substring fallback), normalize_part(raw, object_type) context-aware
    │   ├── openrouter.py          ✅ Phase 2+fix: API wrapper + retry (3× exponential backoff), json_response flag for multimodal
    │   └── precheck.py            ✅ Phase 3: OpenCV pre-checks (corrupt / too_small / extreme_blur)
    ├── tests/
    │   ├── test_core.py           ✅ Phase 1: 49 tests covering models, signals, taxonomy, loader
    │   ├── test_agent1.py         ✅ Phase 2: 6 tests (fast-path, LLM fallback, hi/es, injection, multi-part)
    │   ├── test_agents_3_4.py     ✅ Phase 3: 10 tests (vision, quality, evidence, precheck)
    │   ├── test_agents_5_6.py     ✅ Phase 4: 13 tests (fusion 8, validator 3, history risk 2)
    │   ├── test_agents_7_8.py     ✅ Phase 5: 6 tests (3 decision branches, 3 audit rules)
    │   ├── test_pipeline_e2e.py   ✅ Phase 6: 28 tests (14 formatter + 14 E2E)
    │   └── test_evaluation.py     ✅ Phase 7: 28 tests (9 metrics + 3 confusion matrix + 9 report + 4 ablation + 3 edge case)
    └── evaluation/
        ├── main.py                ✅ Phase 7: evaluation runner (real/synthetic modes, 2 ablation strategies)
        ├── metrics.py             ✅ Phase 7: per-field accuracy, macro F1, confusion matrix
        └── evaluation_report.md   ✅ Phase 7: generated report with metrics, comparisons, operational analysis
```

---

## Branching + DevOps workflow

Cut each branch from `main` after previous PR merges.  
Pattern: `git checkout main && git pull && git checkout -b phase/N-name`

| Phase | Branch | Goal |
|-------|--------|------|
| 0 | `phase/0-skeleton` | Folder structure, all stubs, context.md |
| 1 | `phase/1-core-models` | Pydantic models, config, loader, signal detector, taxonomy |
| 2 | `phase/2-agent1-claim-parser` | Hybrid claim parser: regex fast path + LLM fallback |
| 3 | `phase/3-agents2-3-4-vision` | Agents 2, 3, 4 — vision + quality with cost-aware routing |
| 4 | `phase/4-agent5-fusion-validator-risk` | Agent 5 (deterministic fusion) + Agent 5b (object-part validator) + Agent 6 |
| 5 | `phase/5-agents7-8-decision-audit` | Agents 7, 8 — decision + enhanced audit orchestrator |
| 6 | `phase/6-pipeline-e2e` | Full pipeline → output.csv |
| 7 | `phase/7-evaluation` | Evaluation on sample set + report |
| 8 | `phase/8-submission` | Hardening, final run, code.zip |

---

## Tests

Run all: `pytest code/tests/ -v`

Each phase adds tests in `code/tests/test_phase_N.py`.  
Tests must pass before PR is opened.

Phase 1 test suite: **49 tests, all passing**
Phase 2 test suite: **6 tests** (fast-path, LLM fallback, hi/es, injection, multi-part)
Phase 3 test suite: **10 tests** (vision struct, quality struct, parallelism, evidence lookup, 2x fuzzy fallback, 3x cost-aware routing, integration)
Phase 4 test suite: **13 tests** (fusion 8, validator 3, history risk 2)

Phase 5 test suite: **6 tests** (3 decision branches, 3 audit rules)

Phase 6 test suite: **28 tests** (14 CSV formatter + 14 pipeline E2E)

Phase 7 test suite: **28 tests** (9 metrics + 3 confusion matrix + 9 report validation + 4 ablation + 3 edge case)

**Total: 140 tests, all passing** (`PYTHONPATH=code python -m pytest code/tests/ -v`)

---

## Current status

**Completed phases:** Phase 0 ✅, Phase 1 ✅, Phase 2 ✅, Phase 3 ✅, Phase 4 ✅, Phase 5 ✅, Phase 6 ✅, Phase 7 ✅, Phase 8 ✅
**In progress:** —
**Output:** `output.csv` at repo root — 44 rows, 14 columns, 0 schema errors (validated)
**Evaluation report:** `code/evaluation/evaluation_report.md` — generated in real + synthetic modes
**code.zip:** Built — contains full `code/` tree, excludes `__pycache__`, `*.pyc`, `.env`
**Tests:** 140 tests, all passing (`PYTHONPATH=code python -m pytest code/tests/ -v`)

### Phase 8 evaluation metrics (real mode, sample set, without local images)

> NOTE: Images are only available in the HackerRank sandbox. Without `dataset/images/`,
> all VLM calls are skipped via cost-aware routing (precheck → `valid_image=false`).
> `claim_status` defaults to `not_enough_information`. `object_part` accuracy (0.75)
> reflects Agent 1 text-only extraction performance.

| Field | Accuracy | Notes |
|-------|----------|-------|
| claim_status | 0.1500 | Baseline: all `not_enough_information` (no images locally) |
| issue_type | 0.1500 | Same reason; defaults to `unknown` |
| object_part | **0.7500** | Agent 1 correctly extracts claimed part from text alone |
| severity | 0.1500 | Defaults to `unknown` without visual evidence |
| evidence_standard_met | 0.1500 | All `false` without images |
| valid_image | 0.1500 | All `false` without images |

### Phase 8 hardening changes
- Fixed `main.py` output path bug: used 3 `dirname` calls instead of 2, writing `output.csv` to parent of repo root instead of repo root. Fixed by importing `REPO_ROOT` from `code.core.config`.
- Added `load_dotenv` in `code/main.py` and `code/evaluation/main.py` to auto-load `code/.env` so the API key is available without manual `export`.
- Added context note to `evaluation_report.md` generator explaining image-environment limitations.
- Wrote `README.md` for GitHub with full architecture, setup, usage, and results documentation.

---

## Key decisions + rationale (for judge interview)

1. **Vision model asks only "what is visible?" — never "is the claim valid?"**  
   Eliminates hallucinated decisions. All verdict logic lives in the deterministic rule engine.

2. **Agents 3+4 run in parallel per image using asyncio.gather**  
   Minimizes latency without exceeding rate limits.

3. **Agent 6 (history risk) never modifies claim_status**  
   Exactly per problem_statement.md. History adds context only.

4. **Agent 8 (audit) re-runs individual agents, not the full pipeline**  
   Targeted recovery — faster and cheaper than restarting.

5. **Temperature 0.1 for all LLM calls**  
   Low randomness → consistent structured JSON output.

6. **Taxonomy normalizer runs before any LLM call**  
   Prevents VLM slang ("shattered display") from reaching output columns.

7. **Signal detector runs before Agent 1**  
   Prompt injection is detected independently of the LLM — the LLM cannot be tricked  
   into approving claims because the flag is set deterministically by Layer 1.

8. **Agent 5 (cross-image fusion) is deterministic, not an LLM**  
   Fusion is aggregation of structured findings, not reasoning. Computing  
   `target_part_visible` is a simple boolean OR over valid images. No model call needed —  
   cheaper, faster, easier to test, deterministic.

9. **Agent 1 is hybrid: regex fast path + LLM fallback**  
   Simple English claims ("rear bumper scratch") never hit Gemini. LLM only fires for  
   multilingual, complex, or multi-part claims. Massively reduces token usage.

10. **Confidence scores on every agent output (internal only)**  
    Every agent returns `confidence: float 0.0–1.0`. Audit triggers re-run when  
    confidence < 0.65. Enables targeted recovery without full pipeline restart.

11. **Cost-aware routing: OpenCV pre-checks before any VLM call**  
    Corrupt, extremely blurry, or undersized images are rejected by OpenCV before  
    reaching Gemini. Saves ~20-30% of vision API calls.

12. **Evidence coverage score as a hidden decision variable**  
    `coverage = (images showing claimed_part) / (total valid images)`.  
    When coverage < threshold (e.g., 0.5), decision defaults to  
    `not_enough_information`. Prevents overconfident supported/contradicted verdicts  
    on partial evidence.

13. **Object-Part Validator (Agent 5b) prevents schema violations**  
    A tiny deterministic agent after vision extraction catches impossible combinations  
    like `car + keyboard` and auto-corrects to `unknown`. Zero model calls, zero cost,  
    prevents all schema violations at the output layer.

14. **`damage_consistent` checks claimed_issue matches detected type (not just internal consistency)**  
    Original logic: True if ≤1 damage type detected. Bug: claim="dent", image shows "scratch" → consistent=True → wrongly "supported".  
    Fixed: `consistent = (len(types)==1) AND (claimed_issue in types)`. Multiple types OR wrong type → False → "contradicted".

15. **`normalize_part(raw, object_type)` is context-aware**  
    "corner" → "corner" (laptop) vs "package_corner" (package). LLM sometimes returns "car_door" — stripped of object prefix and re-normalised.

16. **`response_format=json_object` disabled for multimodal VLM calls**  
    Gemini via OpenRouter may reject the parameter when the payload includes image data. Vision agents use `json_response=False`; text-only agents keep json mode.

17. **GitHub default branch set to `main`**  
    Phases 1–3 PRs merged into `phase/0-skeleton` (old default). Fixed by setting default branch via GitHub API. All 84 tests pass on `main`.
