import pytest

from code.agents.decision_engine import decide
from code.agents.audit_recovery import audit
from code.core.models import (
    FusedEvidence, CanonicalClaim, RiskAssessment, Decision, ClaimCase, AuditResult,
)


class TestDecisionEngine:
    def test_decision_supported(self):
        fused = FusedEvidence(
            target_part_visible=True,
            damage_visible=True,
            damage_consistent=True,
            evidence_standard_met=True,
            evidence_standard_met_reason="Part visible with 100% coverage.",
            evidence_coverage_score=1.0,
            supporting_image_ids=["img_1", "img_2"],
            valid_image=True,
            confidence=0.9,
        )
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        risk = RiskAssessment(risk_flags=["none"])

        result = decide(fused, canonical, risk)

        assert isinstance(result, Decision)
        assert result.claim_status == "supported"
        assert result.issue_type == "dent"
        assert result.object_part == "front_bumper"
        assert result.severity == "high"
        assert "supports the claim" in result.claim_status_justification.lower()
        assert "img_1" in result.claim_status_justification

    def test_decision_contradicted(self):
        fused = FusedEvidence(
            target_part_visible=True,
            damage_visible=True,
            damage_consistent=False,
            evidence_standard_met=True,
            evidence_standard_met_reason="Part visible with 100% coverage.",
            evidence_coverage_score=1.0,
            supporting_image_ids=["img_1"],
            valid_image=True,
            confidence=0.7,
        )
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="rear_bumper")
        risk = RiskAssessment()

        result = decide(fused, canonical, risk)

        assert isinstance(result, Decision)
        assert result.claim_status == "contradicted"
        assert result.issue_type == "dent"
        assert result.object_part == "rear_bumper"
        assert result.severity == "low"
        assert "does not match" in result.claim_status_justification

    def test_decision_not_enough_info(self):
        fused = FusedEvidence(
            target_part_visible=False,
            damage_visible=False,
            damage_consistent=True,
            evidence_standard_met=False,
            evidence_standard_met_reason="Claimed part not visible in any valid image (coverage=0%).",
            evidence_coverage_score=0.0,
            supporting_image_ids=["img_1"],
            valid_image=False,
            confidence=0.0,
        )
        canonical = CanonicalClaim(claimed_issue="scratch", claimed_part="hood")
        risk = RiskAssessment()

        result = decide(fused, canonical, risk)

        assert isinstance(result, Decision)
        assert result.claim_status == "not_enough_information"
        assert result.issue_type == "unknown"
        assert result.object_part == "hood"
        assert result.severity == "unknown"
        assert "not provide enough evidence" in result.claim_status_justification


class TestAuditRecovery:
    def test_audit_catches_severity_mismatch(self):
        fused = FusedEvidence(
            target_part_visible=False,
            evidence_standard_met=False,
            evidence_standard_met_reason="No part visible.",
            confidence=0.3,
        )
        canonical = CanonicalClaim(
            claimed_issue="dent",
            claimed_part="front_bumper",
        )
        risk = RiskAssessment(risk_flags=["none"])
        decision = Decision(
            claim_status="not_enough_information",
            claim_status_justification="test",
            issue_type="unknown",
            object_part="front_bumper",
            severity="high",
        )
        case = ClaimCase(
            user_id="user_01",
            canonical_claim=canonical,
            fused_evidence=fused,
            risk_assessment=risk,
            decision=decision,
        )

        result = audit(case)

        assert isinstance(result, AuditResult)
        assert result.passed is False
        assert any("severity" in inc for inc in result.inconsistencies)
        assert "decision" in result.rerun_agents

    def test_audit_catches_contradicted_without_part(self):
        fused = FusedEvidence(
            target_part_visible=False,
            damage_visible=True,
            damage_consistent=False,
            evidence_standard_met=True,
            confidence=0.8,
        )
        canonical = CanonicalClaim(
            claimed_issue="scratch",
            claimed_part="door",
        )
        risk = RiskAssessment()
        decision = Decision(
            claim_status="contradicted",
            claim_status_justification="test",
            issue_type="scratch",
            object_part="door",
            severity="low",
        )
        case = ClaimCase(
            user_id="user_02",
            canonical_claim=canonical,
            fused_evidence=fused,
            risk_assessment=risk,
            decision=decision,
        )

        result = audit(case)

        assert isinstance(result, AuditResult)
        assert result.passed is False
        assert any("should be NEI" in inc for inc in result.inconsistencies)
        assert "decision" in result.rerun_agents

    def test_audit_catches_low_confidence(self):
        fused = FusedEvidence(
            target_part_visible=True,
            damage_visible=True,
            damage_consistent=True,
            evidence_standard_met=True,
            confidence=0.45,
        )
        canonical = CanonicalClaim(
            claimed_issue="dent",
            claimed_part="front_bumper",
        )
        risk = RiskAssessment()
        decision = Decision(
            claim_status="supported",
            claim_status_justification="test",
            issue_type="dent",
            object_part="front_bumper",
            severity="medium",
        )
        case = ClaimCase(
            user_id="user_03",
            canonical_claim=canonical,
            fused_evidence=fused,
            risk_assessment=risk,
            decision=decision,
        )

        result = audit(case)

        assert isinstance(result, AuditResult)
        assert result.passed is False
        assert any("confidence" in inc for inc in result.inconsistencies)
        assert "vision" in result.rerun_agents