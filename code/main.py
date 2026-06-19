"""Full pipeline entry point. Run: python code/main.py"""

import os
import sys
import asyncio
import traceback
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

# Load .env from code/ directory (where the .env file lives)
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_ENV_PATH)

from code.core.config import DATASET_DIR, REPO_ROOT
from code.core.loader import DataLoader
from code.core.models import (
    ClaimCase, CanonicalClaim, EvidenceRequirement,
    ImageFindings, ImageQuality, FusedEvidence,
    RiskAssessment, Decision, AuditResult,
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


MAX_AUDIT_RETRIES = 1


def _resolve_image_paths(raw_paths: str) -> list[str]:
    """Split semicolon-separated image paths and resolve to absolute."""
    return [p.strip() for p in raw_paths.split(";") if p.strip()]


def _full_path(relative: str) -> str:
    return os.path.join(DATASET_DIR, relative)


async def _run_vision_for_image(
    vision_agent: VisionEvidenceAgent,
    quality_agent: ImageQualityAgent,
    full_path: str,
    claim_object: str,
    claimed_issue: str,
    claimed_part: str,
) -> tuple[ImageFindings, ImageQuality]:
    """Run Agents 3 and 4 in parallel for a single image."""
    finding, quality = await asyncio.gather(
        vision_agent.run(full_path, claim_object, claimed_issue, claimed_part),
        quality_agent.run(full_path),
    )
    return finding, quality


def _precheck_skip_result(full_path: str) -> tuple[ImageFindings, ImageQuality]:
    """Deterministic result when precheck fails — skip VLM entirely."""
    image_id = full_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    finding = ImageFindings(
        image_id=image_id,
        object_visible=False,
        visible_parts=[],
        issue_detected=None,
        issue_severity="unknown",
        confidence=0.0,
    )
    quality = ImageQuality(
        image_id=image_id,
        valid=False,
        confidence=1.0,
    )
    return finding, quality


async def process_row(row: dict, loader: DataLoader) -> Optional[dict]:
    """Run the full pipeline for a single claims.csv row.

    Returns a dict with 14 output columns, or None if processing fails.
    """
    user_id = row["user_id"]
    claim_object = row["claim_object"]
    user_claim = row["user_claim"]
    image_paths = _resolve_image_paths(row["image_paths"])

    formatter = CSVFormatter()

    # ── Layer 1: Signal detection ────────────────────────────────────
    detector = SignalDetector()
    signals = detector.scan(user_claim)

    # ── Agent 1: Hybrid claim parser ─────────────────────────────────
    parser = ClaimParserAgent()
    canonical = await parser.run(
        user_claim,
        claim_object,
        detected_language=signals.language,
        prompt_injection=signals.prompt_injection,
    )

    # ── Agent 2: Evidence requirement ────────────────────────────────
    evidence_agent = EvidenceRequirementAgent()
    evidence_req = evidence_agent.lookup(claim_object, canonical.claimed_issue)

    # ── Cost-aware routing + Agents 3 & 4 ────────────────────────────
    vision_agent = VisionEvidenceAgent()
    quality_agent = ImageQualityAgent()

    findings: list[ImageFindings] = []
    quality_results: list[ImageQuality] = []

    for rel_path in image_paths:
        full = _full_path(rel_path)
        precheck = precheck_image(full)
        if not precheck["valid"]:
            f, q = _precheck_skip_result(full)
            findings.append(f)
            quality_results.append(q)
        else:
            f, q = await _run_vision_for_image(
                vision_agent, quality_agent, full,
                claim_object, canonical.claimed_issue, canonical.claimed_part,
            )
            findings.append(f)
            quality_results.append(q)

    # ── Agent 5: Cross-image fusion ──────────────────────────────────
    fused = fuse(findings, quality_results, canonical, evidence_req)

    # ── Agent 5b: Object-part validation ─────────────────────────────
    canonical.claimed_part = validate_part(claim_object, canonical.claimed_part)
    canonical.claimed_issue = validate_issue(claim_object, canonical.claimed_issue)

    # ── Agent 6: History risk ────────────────────────────────────────
    history_agent = HistoryRiskAgent()
    risk = history_agent.assess_risk(user_id)

    # ── Agent 7: Decision engine ─────────────────────────────────────
    decision = decide(fused, canonical, risk)

    # ── Build initial case for audit ─────────────────────────────────
    case = ClaimCase(
        user_id=user_id,
        image_paths=image_paths,
        user_claim=user_claim,
        claim_object=claim_object,
        prompt_injection=signals.prompt_injection,
        threat_language=signals.threat_language,
        detected_language=signals.language,
        canonical_claim=canonical,
        evidence_requirement=evidence_req,
        image_findings=findings,
        image_quality=quality_results,
        fused_evidence=fused,
        risk_assessment=risk,
        decision=decision,
    )

    # ── Agent 8: Audit & Recovery ────────────────────────────────────
    for _ in range(MAX_AUDIT_RETRIES + 1):
        audit_result = audit(case)
        if audit_result.passed:
            break
        # Targeted re-run: re-execute decision with audit-informed fixes
        rerun = audit_result.rerun_agents
        if "vision" in rerun:
            new_findings = []
            new_quality = []
            for f, q in zip(case.image_findings, case.image_quality):
                if q.confidence < 0.65:
                    rel_path = next(
                        (ip for ip in image_paths if ip.rsplit("/", 1)[-1].startswith(f.image_id)),
                        None,
                    )
                    if rel_path:
                        full = _full_path(rel_path)
                        nf, nq = await _run_vision_for_image(
                            vision_agent, quality_agent, full,
                            claim_object, canonical.claimed_issue, canonical.claimed_part,
                        )
                        new_findings.append(nf)
                        new_quality.append(nq)
                    else:
                        new_findings.append(f)
                        new_quality.append(q)
                else:
                    new_findings.append(f)
                    new_quality.append(q)
            case.image_findings = new_findings
            case.image_quality = new_quality
        if "fusion" in rerun or "decision" in rerun:
            case.fused_evidence = fuse(
                case.image_findings, case.image_quality,
                case.canonical_claim, case.evidence_requirement,
            )
        if "decision" in rerun:
            case.decision = decide(case.fused_evidence, case.canonical_claim, case.risk_assessment)
        case.audit_result = audit_result

    case.audit_result = audit(case)

    return formatter.format(case)


async def main():
    loader = DataLoader()
    rows = list(loader.claims)
    print(f"Loaded {len(rows)} claims. Processing...")

    results = []
    for i, row in enumerate(rows):
        try:
            result = await process_row(row, loader)
            if result is not None:
                results.append(result)
            print(f"  [{i + 1}/{len(rows)}] {row['user_id']} — "
                  f"{result['claim_status'] if result else 'FAILED'}")
        except Exception:
            print(f"  [{i + 1}/{len(rows)}] {row['user_id']} — ERROR")
            traceback.print_exc()

    df = pd.DataFrame(results, columns=CSVFormatter().columns)
    output_path = os.path.join(REPO_ROOT, "output.csv")
    df.to_csv(output_path, index=False)
    print(f"\nWrote {len(df)} rows to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
