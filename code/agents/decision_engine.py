from code.core.models import FusedEvidence, CanonicalClaim, RiskAssessment, Decision


def _infer_severity(fused: FusedEvidence) -> str:
    if fused.confidence >= 0.8:
        return "high"
    elif fused.confidence >= 0.5:
        return "medium"
    elif fused.confidence > 0:
        return "low"
    return "unknown"


def decide(fused: FusedEvidence, canonical: CanonicalClaim,
           risk: RiskAssessment) -> Decision:

    # ── Contradiction path (checked BEFORE evidence_standard_met gate) ──
    # If the claimed part IS visible but damage is not consistent, that is
    # a contradiction regardless of coverage score.  We should not hide
    # contradictions behind "not_enough_information" just because only one
    # image showed the part.
    if (fused.target_part_visible
            and not fused.damage_consistent
            and fused.evidence_coverage_score > 0):
        return Decision(
            claim_status="contradicted",
            claim_status_justification=(
                f"The {canonical.claimed_part} is visible in the submitted images, "
                f"but the visible evidence does not match the claimed {canonical.claimed_issue}. "
                f"Reviewed images: {', '.join(fused.supporting_image_ids) or 'none'}."
            ),
            issue_type=canonical.claimed_issue,
            object_part=canonical.claimed_part,
            severity="low"
        )

    # ── Evidence gate ──────────────────────────────────────────────────
    if not fused.evidence_standard_met:
        return Decision(
            claim_status="not_enough_information",
            claim_status_justification=(
                f"{fused.evidence_standard_met_reason} "
                f"The submitted images do not provide enough evidence "
                f"to evaluate the {canonical.claimed_part} claim."
            ),
            issue_type="unknown",
            object_part=canonical.claimed_part,
            severity="unknown"
        )

    # ── Supported path ─────────────────────────────────────────────────
    if fused.damage_visible and fused.damage_consistent:
        return Decision(
            claim_status="supported",
            claim_status_justification=(
                f"The image evidence supports the {canonical.claimed_issue} claim "
                f"on {canonical.claimed_part}. "
                f"Supporting images: {', '.join(fused.supporting_image_ids)}."
            ),
            issue_type=canonical.claimed_issue,
            object_part=canonical.claimed_part,
            severity=_infer_severity(fused)
        )

    # ── Fallback NEI ───────────────────────────────────────────────────
    return Decision(
        claim_status="not_enough_information",
        claim_status_justification="Unable to verify claim from submitted images.",
        issue_type="unknown",
        object_part=canonical.claimed_part,
        severity="unknown"
    )
