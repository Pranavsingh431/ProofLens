from code.core.models import ClaimCase, AuditResult


AUDIT_RULES = [
    lambda c: (
        f"issue_type mismatch: claimed={c.canonical_claim.claimed_issue}, "
        f"decision={c.decision.issue_type}"
        if (c.canonical_claim and c.decision and c.fused_evidence
            and c.fused_evidence.evidence_standard_met
            and c.decision.issue_type not in (c.canonical_claim.claimed_issue, "unknown"))
        else None
    ),
    lambda c: (
        f"contradicted but claimed part not visible: "
        f"claimed={c.canonical_claim.claimed_part}"
        if (c.canonical_claim and c.decision and c.fused_evidence
            and c.decision.claim_status == "contradicted"
            and not c.fused_evidence.target_part_visible)
        else None
    ),
    lambda c: (
        "contradicted without target_part_visible → should be NEI"
        if (c.decision and c.fused_evidence
            and c.decision.claim_status == "contradicted"
            and not c.fused_evidence.target_part_visible)
        else None
    ),
    lambda c: (
        f"vision confidence below threshold: "
        f"avg={c.fused_evidence.confidence:.2f} < 0.65"
        if (c.fused_evidence and c.fused_evidence.confidence < 0.65)
        else None
    ),
    lambda c: (
        "severity should be unknown when evidence not met"
        if (c.decision and c.fused_evidence
            and not c.fused_evidence.evidence_standard_met
            and c.decision.severity not in ("unknown",))
        else None
    ),
    lambda c: (
        "supporting_image_ids should be empty for NEI"
        if (c.decision and c.fused_evidence
            and c.decision.claim_status == "not_enough_information"
            and c.fused_evidence.supporting_image_ids not in ([], ["none"]))
        else None
    ),
    lambda c: (
        "text_instruction_present flag missing for injection case"
        if (c.canonical_claim and c.risk_assessment
            and c.canonical_claim.prompt_injection_detected
            and "text_instruction_present" not in c.risk_assessment.risk_flags)
        else None
    ),
]


def audit(case: ClaimCase) -> AuditResult:
    inconsistencies = []
    rerun_agents = set()
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
        rerun_agents=list(rerun_agents)
    )