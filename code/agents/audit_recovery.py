from code.core.models import ClaimCase, AuditResult


def _check_issue_mismatch(c: ClaimCase):
    if (c.canonical_claim and c.decision and c.fused_evidence
            and c.fused_evidence.evidence_standard_met
            and c.decision.issue_type not in (c.canonical_claim.claimed_issue, "unknown")):
        return (
            f"issue_type mismatch: claimed={c.canonical_claim.claimed_issue}, "
            f"decision={c.decision.issue_type}"
        )
    return None


def _check_contradicted_part_not_visible(c: ClaimCase):
    if (c.canonical_claim and c.decision and c.fused_evidence
            and c.decision.claim_status == "contradicted"
            and not c.fused_evidence.target_part_visible):
        return (
            f"contradicted but claimed part not visible: "
            f"claimed={c.canonical_claim.claimed_part}"
        )
    return None


def _check_contradicted_should_be_nei(c: ClaimCase):
    if (c.decision and c.fused_evidence
            and c.decision.claim_status == "contradicted"
            and not c.fused_evidence.target_part_visible):
        return "contradicted without target_part_visible \u2192 should be NEI"
    return None


def _check_low_confidence(c: ClaimCase):
    if c.fused_evidence and c.fused_evidence.confidence < 0.65:
        return (
            f"vision confidence below threshold: "
            f"avg={c.fused_evidence.confidence:.2f} < 0.65"
        )
    return None


def _check_severity_when_nei(c: ClaimCase):
    if (c.decision and c.fused_evidence
            and not c.fused_evidence.evidence_standard_met
            and c.decision.severity not in ("unknown",)):
        return "severity should be unknown when evidence not met"
    return None


def _check_supporting_ids_for_nei(c: ClaimCase):
    if (c.decision and c.fused_evidence
            and c.decision.claim_status == "not_enough_information"
            and c.fused_evidence.supporting_image_ids not in ([], ["none"])):
        return "supporting_image_ids should be empty for NEI"
    return None


def _check_injection_flag(c: ClaimCase):
    if (c.canonical_claim and c.risk_assessment
            and c.canonical_claim.prompt_injection_detected
            and "text_instruction_present" not in c.risk_assessment.risk_flags):
        return "text_instruction_present flag missing for injection case"
    return None


AUDIT_RULES = [
    _check_issue_mismatch,
    _check_contradicted_part_not_visible,
    _check_contradicted_should_be_nei,
    _check_low_confidence,
    _check_severity_when_nei,
    _check_supporting_ids_for_nei,
    _check_injection_flag,
]


def audit(case: ClaimCase) -> AuditResult:
    """Run all 7 audit rules. On failure, determine minimal agents to re-run."""
    inconsistencies = []
    rerun_agents: set[str] = set()

    for rule in AUDIT_RULES:
        result = rule(case)
        if result:
            inconsistencies.append(result)
            if "confidence" in result:
                rerun_agents.add("vision")
            elif "mismatch" in result:
                rerun_agents.add("fusion")
                rerun_agents.add("decision")
            else:
                rerun_agents.add("decision")

    return AuditResult(
        passed=len(inconsistencies) == 0,
        inconsistencies=inconsistencies,
        rerun_agents=sorted(rerun_agents),
    )
