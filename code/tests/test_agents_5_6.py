import pytest

from code.agents.history_risk import HistoryRiskAgent
from code.agents.cross_image_fusion import fuse
from code.agents.object_part_validator import validate_part, validate_issue
from code.core.models import (
    ImageFindings, ImageQuality, CanonicalClaim,
    EvidenceRequirement, RiskAssessment, FusedEvidence,
)


class TestHistoryRisk:
    def test_history_risk_high_risk_user(self):
        agent = HistoryRiskAgent()
        result = agent.assess_risk("user_034")
        assert isinstance(result, RiskAssessment)
        assert "user_history_risk" in result.risk_flags
        assert result.user_history_risk is True

    def test_history_risk_unknown_user(self):
        agent = HistoryRiskAgent()
        result = agent.assess_risk("user_nonexistent")
        assert isinstance(result, RiskAssessment)
        assert result.risk_flags == ["none"]
        assert result.user_history_risk is False


class TestFusion:
    def test_fusion_single_supporting_image(self):
        findings = [
            ImageFindings(image_id="img_1", object_visible=True,
                          visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
            ImageFindings(image_id="img_2", object_visible=True,
                          visible_parts=[], issue_detected=None, confidence=0.5),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True, confidence=1.0),
            ImageQuality(image_id="img_2", valid=False, blurry=True, confidence=0.0),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert isinstance(result, FusedEvidence)
        assert result.target_part_visible is True
        assert result.evidence_coverage_score == 1.0
        assert result.confidence == 0.9
        assert result.evidence_standard_met is True
        assert "img_1" in result.supporting_image_ids
        assert "img_2" not in result.supporting_image_ids

    def test_fusion_no_valid_images(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=False, blurry=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.target_part_visible is False
        assert result.evidence_standard_met is False
        assert result.valid_image is False

    def test_fusion_inconsistent_damage(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
            ImageFindings(image_id="img_2", visible_parts=["front_bumper"],
                          issue_detected="scratch", confidence=0.8),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True),
            ImageQuality(image_id="img_2", valid=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.damage_consistent is False

    def test_fusion_partial_coverage(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
            ImageFindings(image_id="img_2", visible_parts=["hood"],
                          issue_detected="scratch", confidence=0.7),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True),
            ImageQuality(image_id="img_2", valid=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.evidence_coverage_score == 0.5
        assert result.evidence_standard_met is True

    def test_fusion_low_coverage(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
            ImageFindings(image_id="img_2", visible_parts=["hood"],
                          issue_detected=None, confidence=0.5),
            ImageFindings(image_id="img_3", visible_parts=[],
                          issue_detected=None, confidence=0.3),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True),
            ImageQuality(image_id="img_2", valid=True),
            ImageQuality(image_id="img_3", valid=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.evidence_coverage_score == 0.33
        assert result.evidence_standard_met is False

    def test_fusion_confidence_weighted(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.9),
            ImageFindings(image_id="img_2", visible_parts=["front_bumper"],
                          issue_detected="dent", confidence=0.7),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True),
            ImageQuality(image_id="img_2", valid=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.confidence == 0.8

    def test_fusion_no_damage_images_still_supporting(self):
        findings = [
            ImageFindings(image_id="img_1", visible_parts=["front_bumper"],
                          issue_detected=None, confidence=0.9),
        ]
        quality = [
            ImageQuality(image_id="img_1", valid=True),
        ]
        canonical = CanonicalClaim(claimed_issue="dent", claimed_part="front_bumper")
        evidence_req = EvidenceRequirement(
            object_type="car", issue_type="dent",
            minimum_image_evidence="foo", applies_to="dent",
        )
        result = fuse(findings, quality, canonical, evidence_req)
        assert result.target_part_visible is True
        assert result.damage_visible is False
        assert "img_1" in result.supporting_image_ids


class TestObjectPartValidator:
    def test_object_part_validator_car(self):
        assert validate_part("car", "front_bumper") == "front_bumper"
        assert validate_part("car", "keyboard") == "unknown"

    def test_object_part_validator_laptop(self):
        assert validate_part("laptop", "screen") == "screen"
        assert validate_part("laptop", "hood") == "unknown"

    def test_object_part_validator_package(self):
        assert validate_part("package", "seal") == "seal"
        assert validate_part("package", "door") == "unknown"

    def test_validate_issue(self):
        assert validate_issue("car", "dent") == "dent"
        assert validate_issue("laptop", "crack") == "crack"
        assert validate_issue("package", "stain") == "stain"
        assert validate_issue("car", "explosion") == "unknown"
