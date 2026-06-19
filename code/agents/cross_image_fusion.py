from code.core.models import ImageFindings, ImageQuality, CanonicalClaim, EvidenceRequirement, FusedEvidence


def fuse(findings: list[ImageFindings], quality: list[ImageQuality],
          canonical: CanonicalClaim, evidence_req: EvidenceRequirement) -> FusedEvidence:
    quality_map = {q.image_id: q for q in quality}

    valid_findings = [f for f in findings
                      if quality_map.get(f.image_id, ImageQuality()).valid]

    target_part_visible = any(
        canonical.claimed_part in f.visible_parts
        for f in valid_findings
    )

    damage_visible = any(f.issue_detected is not None for f in valid_findings)

    part_findings = [f for f in valid_findings
                     if canonical.claimed_part in f.visible_parts]
    damage_types = set(f.issue_detected for f in part_findings
                      if f.issue_detected is not None)
    damage_consistent = len(damage_types) <= 1 if damage_types else True

    total_valid = max(len(valid_findings), 1)
    coverage = len(part_findings) / total_valid

    evidence_standard_met = target_part_visible and coverage >= 0.5

    supporting = [
        f.image_id for f in valid_findings
        if canonical.claimed_part in f.visible_parts
        and (f.issue_detected is not None
             or quality_map.get(f.image_id, ImageQuality()).valid)
    ]

    confidences = [f.confidence for f in part_findings]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return FusedEvidence(
        target_part_visible=target_part_visible,
        damage_visible=damage_visible,
        damage_consistent=damage_consistent,
        evidence_standard_met=evidence_standard_met,
        evidence_standard_met_reason=_build_reason(target_part_visible, coverage),
        evidence_coverage_score=round(coverage, 2),
        supporting_image_ids=supporting if supporting else [],
        valid_image=total_valid > 0 and len(valid_findings) > 0,
        confidence=round(avg_confidence, 2)
    )


def _build_reason(part_visible: bool, coverage: float) -> str:
    if not part_visible:
        return f"Claimed part not visible in any valid image (coverage={coverage:.0%})."
    if coverage < 0.5:
        return f"Claimed part partially visible (coverage={coverage:.0%})."
    return f"Claimed part visible with {coverage:.0%} coverage."