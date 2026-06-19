from code.core.models import ImageFindings, ImageQuality, CanonicalClaim, EvidenceRequirement, FusedEvidence


def _part_matches(claimed: str, visible: list[str]) -> bool:
    """Fuzzy match claimed_part against visible_parts list.

    Gemini may return 'rear bumper' when canonical part is 'rear_bumper',
    or 'bumper' as a short form. Accept substring matches in both directions.
    """
    claimed_norm = claimed.lower().replace("_", " ")
    for p in visible:
        p_norm = p.lower().replace("_", " ")
        if claimed_norm in p_norm or p_norm in claimed_norm:
            return True
    return False


def fuse(findings: list[ImageFindings], quality: list[ImageQuality],
          canonical: CanonicalClaim, evidence_req: EvidenceRequirement) -> FusedEvidence:
    quality_map = {q.image_id: q for q in quality}

    valid_findings = [f for f in findings
                      if quality_map.get(f.image_id, ImageQuality()).valid]

    # Fuzzy part matching — handles 'rear bumper' vs 'rear_bumper', etc.
    target_part_visible = any(
        _part_matches(canonical.claimed_part, f.visible_parts)
        for f in valid_findings
    )

    damage_visible = any(
        f.issue_detected is not None and f.issue_detected != "none"
        for f in valid_findings
    )

    part_findings = [f for f in valid_findings
                     if _part_matches(canonical.claimed_part, f.visible_parts)]
    damage_types = {f.issue_detected for f in part_findings
                    if f.issue_detected is not None and f.issue_detected != "none"}

    # Consistent logic:
    # - No damage types + claim is "none"/"unknown" → consistent (no damage claimed, none seen)
    # - No damage types + damage WAS claimed → INCONSISTENT (claim says damage, image shows none)
    # - Multiple damage types → inconsistent (conflicting evidence)
    # - Single damage type matching claimed issue → consistent
    # - Single damage type NOT matching claimed issue → inconsistent
    if not damage_types:
        if canonical.claimed_issue in ("none", "unknown"):
            damage_consistent = True
        else:
            # Part visible but no damage detected → contradicts a damage claim
            damage_consistent = False
    elif len(damage_types) > 1:
        damage_consistent = False
    else:
        damage_consistent = canonical.claimed_issue in damage_types

    total_valid = max(len(valid_findings), 1)
    coverage = len(part_findings) / total_valid

    # Lower threshold from 0.5 → 0.3:
    # 1 image out of 3 showing the part is meaningful evidence.
    evidence_standard_met = target_part_visible and coverage >= 0.3

    supporting = [
        f.image_id for f in valid_findings
        if _part_matches(canonical.claimed_part, f.visible_parts)
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
    if coverage < 0.3:
        return f"Claimed part visible in only {coverage:.0%} of images — insufficient coverage."
    return f"Claimed part visible with {coverage:.0%} coverage."
