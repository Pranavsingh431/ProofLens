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
│   ├── claims.csv                 ✅ loaded, 44 rows
│   ├── sample_claims.csv          ✅ loaded, 20 rows
│   ├── user_history.csv           ✅ created skeleton, 40 rows
│   ├── evidence_requirements.csv  ✅ created skeleton, 19 rows
│   └── images/sample/ + images/test/  ✅ 111 placeholder image paths
└── code/
    ├── main.py                    ← pipeline entry point
    ├── requirements.txt
    ├── .env.example
    ├── agents/
    │   ├── claim_parser.py        ← Agent 1 ✅ (hybrid: regex + LLM)
    │   ├── evidence_requirement.py← Agent 2 (stub)
    │   ├── vision_evidence.py     ← Agent 3 (stub)
    │   ├── image_quality.py       ← Agent 4 (stub)
    │   ├── cross_image_fusion.py  ← Agent 5 (stub)
    │   ├── object_part_validator.py ← Agent 5b (stub)
    │   ├── history_risk.py        ← Agent 6 (stub)
    │   ├── decision_engine.py     ← Agent 7 (stub)
    │   ├── audit_recovery.py      ← Agent 8 (stub)
    │   └── csv_formatter.py       ← Layer 5 (stub)
    ├── core/
    │   ├── config.py              ✅ Phase 1: paths, models, allowed-value sets
    │   ├── models.py              ✅ Phase 1: 10 Pydantic schemas + confidence fields
    │   ├── loader.py              ✅ Phase 1: DataLoader, 4 CSVs, image path resolution
    │   ├── signal_detector.py     ✅ Phase 1: regex-based injection/threat/language
    │   ├── taxonomy.py            ✅ Phase 1: 78 issue + 40 part normalization mappings
    │   ├── openrouter.py          ✅ Phase 2: API wrapper + retry (3× exponential backoff)
    │   └── precheck.py            ← Phase 3: OpenCV pre-checks
    ├── tests/
    │   ├── test_core.py           ✅ Phase 1: 49 tests covering models, signals, taxonomy, loader
    │   └── test_agent1.py         ✅ Phase 2: 6 tests (fast-path, LLM fallback, hi/es, injection, multi-part)
    └── evaluation/
        ├── main.py
        ├── metrics.py
        └── evaluation_report.md
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

Each phase adds tests in `code/tests/test_core.py`, `code/tests/test_agent1.py`, etc.  
Tests must pass before PR is opened.

Phase 1 test suite: **49 tests, all passing**
Phase 2 test suite: **6 tests** (fast-path, LLM fallback, hi/es, injection, multi-part)

---

## Current status

**Completed phases:** Phase 0 ✅, Phase 1 ✅  
**In progress:** Phase 2 ✅ (PR open: `phase/2-agent1-claim-parser` → `main`)  
**Last evaluation metrics (sample set):**
- claim_status accuracy: —
- issue_type accuracy: —
- object_part accuracy: —
- severity accuracy: —

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
