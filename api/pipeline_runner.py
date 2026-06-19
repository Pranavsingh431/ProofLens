"""
Instrumented pipeline runner.

Mirrors code/main.py but emits structured events after each agent step
so the frontend can visualise real-time progress.
"""

import asyncio
import os
import sys
import time
from typing import Callable, Awaitable

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from code.core.config import DATASET_DIR
from code.core.loader import DataLoader
from code.core.models import (
    ClaimCase, ImageFindings, ImageQuality,
)
from code.core.signal_detector import SignalDetector
from code.core.precheck import precheck_image
from code.agents.claim_parser import ClaimParserAgent
from code.agents.evidence_requirement import EvidenceRequirementAgent
from code.agents.vision_evidence import VisionEvidenceAgent
from code.agents.image_quality import ImageQualityAgent
from code.agents.cross_image_fusion import fuse
from code.agents.object_part_validator import validate_part, validate_issue
from code.agents.history_risk import HistoryRiskAgent
from code.agents.decision_engine import decide
from code.agents.audit_recovery import audit
from code.agents.csv_formatter import CSVFormatter

Emitter = Callable[[dict], Awaitable[None]]


def _full_path(relative: str) -> str:
    return os.path.join(DATASET_DIR, relative)


def _resolve_image_paths(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(";") if p.strip()]


def _precheck_skip_result(full_path: str) -> tuple[ImageFindings, ImageQuality]:
    image_id = full_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return (
        ImageFindings(
            image_id=image_id, object_visible=False, visible_parts=[],
            issue_detected=None, issue_severity="unknown", confidence=0.0,
        ),
        ImageQuality(image_id=image_id, valid=False, confidence=1.0),
    )


async def _run_vision_pair(
    vision_agent: VisionEvidenceAgent,
    quality_agent: ImageQualityAgent,
    full_path: str,
    claim_object: str,
    claimed_issue: str,
    claimed_part: str,
) -> tuple[ImageFindings, ImageQuality]:
    finding, quality = await asyncio.gather(
        vision_agent.run(full_path, claim_object, claimed_issue, claimed_part),
        quality_agent.run(full_path),
    )
    return finding, quality


async def run_pipeline_with_events(row: dict, loader: DataLoader, emit: Emitter):
    """
    Run the full 10-component ProofLens pipeline and emit a structured event
    after each step.

    Event shapes
    ────────────
    {"type": "step_start",    "step": "<id>"}
    {"type": "step_complete", "step": "<id>", "duration_ms": int, "data": {...}}
    {"type": "step_skipped",  "step": "<id>", "reason": str}
    {"type": "pipeline_complete", "output": {<14-col row>}}
    {"type": "error", "message": str, "trace": str}
    """
    user_id      = row["user_id"]
    claim_object = row["claim_object"]
    user_claim   = row["user_claim"]
    image_paths  = _resolve_image_paths(row.get("image_paths", ""))

    formatter = CSVFormatter()

    # ── Layer 1: Signal detection ─────────────────────────────────────
    await emit({"type": "step_start", "step": "signal_detection"})
    t0 = time.monotonic()
    detector = SignalDetector()
    signals  = detector.scan(user_claim)
    await emit({
        "type": "step_complete",
        "step": "signal_detection",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "prompt_injection":  signals.prompt_injection,
            "threat_language":   signals.threat_language,
            "language":          signals.language,
            "flags_raised": (
                (["prompt_injection"] if signals.prompt_injection  else []) +
                (["threat_language"]  if signals.threat_language   else [])
            ),
        },
    })

    # ── Agent 1: Hybrid claim parser ──────────────────────────────────
    await emit({"type": "step_start", "step": "claim_parser"})
    t0 = time.monotonic()
    parser    = ClaimParserAgent()
    canonical = await parser.run(
        user_claim, claim_object,
        detected_language=signals.language,
        prompt_injection=signals.prompt_injection,
    )
    used_llm = (
        canonical.language != "en"
        or canonical.multi_part
        or signals.prompt_injection
        or canonical.confidence < 1.0
    )
    await emit({
        "type": "step_complete",
        "step": "claim_parser",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "claimed_issue":   canonical.claimed_issue,
            "claimed_part":    canonical.claimed_part,
            "language":        canonical.language,
            "multi_part":      canonical.multi_part,
            "secondary_issue": canonical.secondary_issue,
            "secondary_part":  canonical.secondary_part,
            "confidence":      round(canonical.confidence, 3),
            "path":            "llm_fallback" if used_llm else "regex_fast_path",
            "prompt_injection_detected": canonical.prompt_injection_detected,
            "threat_detected": canonical.threat_detected,
        },
    })

    # ── Agent 2: Evidence requirement ─────────────────────────────────
    await emit({"type": "step_start", "step": "evidence_requirement"})
    t0 = time.monotonic()
    ev_agent  = EvidenceRequirementAgent()
    ev_req    = ev_agent.lookup(claim_object, canonical.claimed_issue)
    await emit({
        "type": "step_complete",
        "step": "evidence_requirement",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "minimum_image_evidence": ev_req.minimum_image_evidence,
            "applies_to":             ev_req.applies_to,
            "object_type":            ev_req.object_type,
            "issue_type":             ev_req.issue_type,
        },
    })

    # ── OpenCV pre-checks (cost-aware routing) ────────────────────────
    await emit({"type": "step_start", "step": "precheck"})
    t0 = time.monotonic()
    vision_agent  = VisionEvidenceAgent()
    quality_agent = ImageQualityAgent()

    findings:        list[ImageFindings] = []
    quality_results: list[ImageQuality]  = []
    precheck_data:   list[dict]          = []

    for rel_path in image_paths:
        full = _full_path(rel_path)
        pc   = precheck_image(full)
        img_id = rel_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        precheck_data.append({
            "image_id":   img_id,
            "valid":      pc["valid"],
            "reason":     pc["reason"],
            "dimensions": list(pc["dimensions"]) if pc["dimensions"] != (0, 0) else None,
        })
        if not pc["valid"]:
            f, q = _precheck_skip_result(full)
        else:
            f, q = await _run_vision_pair(
                vision_agent, quality_agent, full,
                claim_object, canonical.claimed_issue, canonical.claimed_part,
            )
        findings.append(f)
        quality_results.append(q)

    valid_count    = sum(1 for d in precheck_data if d["valid"])
    rejected_count = len(precheck_data) - valid_count
    await emit({
        "type": "step_complete",
        "step": "precheck",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "total_images":    len(precheck_data),
            "valid_images":    valid_count,
            "rejected_images": rejected_count,
            "api_calls_saved": rejected_count,
            "images":          precheck_data,
        },
    })

    # ── Agents 3+4: Vision evidence + image quality ───────────────────
    await emit({"type": "step_start", "step": "vision_quality"})
    t0 = time.monotonic()
    vision_summary = []
    for f, q, pc in zip(findings, quality_results, precheck_data):
        vision_summary.append({
            "image_id":           f.image_id,
            "skipped":            not pc["valid"],
            "skip_reason":        pc["reason"] if not pc["valid"] else None,
            "object_visible":     f.object_visible,
            "visible_parts":      f.visible_parts,
            "issue_detected":     f.issue_detected,
            "issue_severity":     f.issue_severity,
            "finding_confidence": round(f.confidence, 3),
            "quality_valid":      q.valid,
            "quality_flags": [
                flag for flag, val in {
                    "blurry":                 q.blurry,
                    "cropped_or_obstructed":  q.cropped_or_obstructed,
                    "low_light_or_glare":     q.low_light_or_glare,
                    "wrong_angle":            q.wrong_angle,
                    "wrong_object":           q.wrong_object,
                    "possible_manipulation":  q.possible_manipulation,
                    "non_original_image":     q.non_original_image,
                    "text_instruction_present": q.text_instruction_present,
                }.items() if val
            ],
            "quality_confidence": round(q.confidence, 3),
        })
    await emit({
        "type": "step_complete",
        "step": "vision_quality",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "images_analysed": valid_count,
            "images_skipped":  rejected_count,
            "images":          vision_summary,
        },
    })

    # ── Agent 5: Cross-image fusion ───────────────────────────────────
    await emit({"type": "step_start", "step": "fusion"})
    t0 = time.monotonic()
    fused = fuse(findings, quality_results, canonical, ev_req)
    await emit({
        "type": "step_complete",
        "step": "fusion",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "target_part_visible":       fused.target_part_visible,
            "damage_visible":            fused.damage_visible,
            "damage_consistent":         fused.damage_consistent,
            "evidence_standard_met":     fused.evidence_standard_met,
            "evidence_standard_met_reason": fused.evidence_standard_met_reason,
            "evidence_coverage_score":   round(fused.evidence_coverage_score, 3),
            "supporting_image_ids":      fused.supporting_image_ids,
            "valid_image":               fused.valid_image,
            "confidence":                round(fused.confidence, 3),
        },
    })

    # ── Agent 5b: Object-part validator ───────────────────────────────
    await emit({"type": "step_start", "step": "object_part_validator"})
    t0 = time.monotonic()
    original_part  = canonical.claimed_part
    original_issue = canonical.claimed_issue
    canonical.claimed_part  = validate_part(claim_object, canonical.claimed_part)
    canonical.claimed_issue = validate_issue(claim_object, canonical.claimed_issue)
    await emit({
        "type": "step_complete",
        "step": "object_part_validator",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "original_part":  original_part,
            "validated_part": canonical.claimed_part,
            "part_changed":   original_part  != canonical.claimed_part,
            "original_issue": original_issue,
            "validated_issue": canonical.claimed_issue,
            "issue_changed":  original_issue != canonical.claimed_issue,
        },
    })

    # ── Agent 6: History risk ─────────────────────────────────────────
    await emit({"type": "step_start", "step": "history_risk"})
    t0 = time.monotonic()
    history_agent = HistoryRiskAgent()
    risk          = history_agent.assess_risk(user_id)
    user_hist     = loader.get_user_history(user_id) or {}
    await emit({
        "type": "step_complete",
        "step": "history_risk",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "risk_flags":        risk.risk_flags,
            "user_history_risk": risk.user_history_risk,
            "user_found":        bool(user_hist),
            "past_claim_count":  user_hist.get("past_claim_count"),
            "rejected_claims":   user_hist.get("rejected_claim"),
            "history_flags":     user_hist.get("history_flags"),
            "history_summary":   user_hist.get("history_summary"),
        },
    })

    # ── Agent 7: Decision engine ──────────────────────────────────────
    await emit({"type": "step_start", "step": "decision_engine"})
    t0 = time.monotonic()
    decision = decide(fused, canonical, risk)
    await emit({
        "type": "step_complete",
        "step": "decision_engine",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "claim_status":               decision.claim_status,
            "claim_status_justification": decision.claim_status_justification,
            "issue_type":                 decision.issue_type,
            "object_part":                decision.object_part,
            "severity":                   decision.severity,
        },
    })

    # ── Build ClaimCase for audit ─────────────────────────────────────
    case = ClaimCase(
        user_id=user_id,
        image_paths=image_paths,
        user_claim=user_claim,
        claim_object=claim_object,
        prompt_injection=signals.prompt_injection,
        threat_language=signals.threat_language,
        detected_language=signals.language,
        canonical_claim=canonical,
        evidence_requirement=ev_req,
        image_findings=findings,
        image_quality=quality_results,
        fused_evidence=fused,
        risk_assessment=risk,
        decision=decision,
    )

    # ── Agent 8: Audit & recovery ─────────────────────────────────────
    await emit({"type": "step_start", "step": "audit"})
    t0 = time.monotonic()
    MAX_RETRIES = 1
    for _ in range(MAX_RETRIES + 1):
        audit_result = audit(case)
        if audit_result.passed:
            break
        rerun = audit_result.rerun_agents
        if "vision" in rerun:
            new_f, new_q = [], []
            for f, q in zip(case.image_findings, case.image_quality):
                if q.confidence < 0.65:
                    rel = next(
                        (ip for ip in image_paths
                         if ip.rsplit("/", 1)[-1].startswith(f.image_id)),
                        None,
                    )
                    if rel:
                        full_ = _full_path(rel)
                        pc_ = precheck_image(full_)
                        if pc_["valid"]:
                            nf, nq = await _run_vision_pair(
                                vision_agent, quality_agent, full_,
                                claim_object, canonical.claimed_issue, canonical.claimed_part,
                            )
                            new_f.append(nf); new_q.append(nq)
                        else:
                            new_f.append(f); new_q.append(q)
                    else:
                        new_f.append(f); new_q.append(q)
                else:
                    new_f.append(f); new_q.append(q)
            case.image_findings  = new_f
            case.image_quality   = new_q
        if "fusion" in rerun or "decision" in rerun:
            case.fused_evidence = fuse(
                case.image_findings, case.image_quality,
                case.canonical_claim, case.evidence_requirement,
            )
        if "decision" in rerun:
            case.decision = decide(
                case.fused_evidence, case.canonical_claim, case.risk_assessment,
            )
        case.audit_result = audit_result

    final_audit = audit(case)
    case.audit_result = final_audit
    await emit({
        "type": "step_complete",
        "step": "audit",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "data": {
            "passed":         final_audit.passed,
            "inconsistencies": final_audit.inconsistencies,
            "rerun_agents":   final_audit.rerun_agents,
        },
    })

    # ── Format + emit final output ────────────────────────────────────
    output_row = formatter.format(case)
    await emit({"type": "pipeline_complete", "output": output_row})
