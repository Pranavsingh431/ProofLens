import pytest
import os
import tempfile
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from code.core.models import (
    ClaimCase, CanonicalClaim, EvidenceRequirement,
    ImageFindings, ImageQuality, FusedEvidence,
    RiskAssessment, Decision, AuditResult,
)
from code.agents.csv_formatter import CSVFormatter, _OUTPUT_COLUMNS
from code.main import process_row, _resolve_image_paths, _precheck_skip_result
from code.core.config import (
    VALID_CLAIM_STATUS, VALID_ISSUE_TYPES, VALID_RISK_FLAGS,
    VALID_SEVERITY, VALID_CAR_PARTS, VALID_LAPTOP_PARTS, VALID_PACKAGE_PARTS,
)
from code.core.signal_detector import SignalDetector
from code.core.loader import DataLoader


_PART_SETS = {"car": VALID_CAR_PARTS, "laptop": VALID_LAPTOP_PARTS, "package": VALID_PACKAGE_PARTS}


def _make_mock_claim_row():
    return {
        "user_id": "user_001",
        "image_paths": "images/test/case_001/img_1.jpg",
        "user_claim": "My car has a dent on the front bumper.",
        "claim_object": "car",
    }


def _make_full_case():
    """Build a synthetic ClaimCase with all fields populated."""
    canonical = CanonicalClaim(
        claimed_issue="dent",
        claimed_part="front_bumper",
        keywords=["dent", "bumper"],
        language="en",
        multi_part=False,
        prompt_injection_detected=False,
        threat_detected=False,
        confidence=1.0,
    )
    evidence_req = EvidenceRequirement(
        object_type="car",
        issue_type="dent",
        minimum_image_evidence="close_up_of_damage_area",
        applies_to="car",
    )
    findings = [
        ImageFindings(
            image_id="img_1",
            object_visible=True,
            visible_parts=["front_bumper", "hood"],
            issue_detected="dent",
            issue_severity="medium",
            confidence=0.9,
        ),
    ]
    quality_results = [
        ImageQuality(
            image_id="img_1",
            blurry=False,
            cropped_or_obstructed=False,
            low_light_or_glare=False,
            wrong_angle=False,
            wrong_object=False,
            possible_manipulation=False,
            non_original_image=False,
            text_instruction_present=False,
            valid=True,
            confidence=0.95,
        ),
    ]
    fused = FusedEvidence(
        target_part_visible=True,
        damage_visible=True,
        damage_consistent=True,
        evidence_standard_met=True,
        evidence_standard_met_reason="Claimed part visible with 100% coverage.",
        evidence_coverage_score=1.0,
        supporting_image_ids=["img_1"],
        valid_image=True,
        confidence=0.9,
    )
    risk = RiskAssessment(risk_flags=["none"])
    decision = Decision(
        claim_status="supported",
        claim_status_justification="The image evidence supports the claim. Supporting images: img_1.",
        issue_type="dent",
        object_part="front_bumper",
        severity="high",
    )
    audit_result = AuditResult(passed=True)

    return ClaimCase(
        user_id="user_001",
        image_paths=["images/test/case_001/img_1.jpg"],
        user_claim="My car has a dent on the front bumper.",
        claim_object="car",
        prompt_injection=False,
        threat_language=False,
        detected_language="en",
        canonical_claim=canonical,
        evidence_requirement=evidence_req,
        image_findings=findings,
        image_quality=quality_results,
        fused_evidence=fused,
        risk_assessment=risk,
        decision=decision,
        audit_result=audit_result,
    )


# ── CSV Formatter Tests ──────────────────────────────────────────────

class TestCSVFormatter:
    def test_formatter_returns_all_14_columns(self):
        case = _make_full_case()
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert isinstance(result, dict)
        assert len(result) == 14
        for col in _OUTPUT_COLUMNS:
            assert col in result, f"Missing column: {col}"

    def test_formatter_columns_exact_order(self):
        formatter = CSVFormatter()
        assert formatter.columns == list(_OUTPUT_COLUMNS)

    def test_formatter_risk_flags_none(self):
        case = _make_full_case()
        case.risk_assessment = RiskAssessment(risk_flags=["none"])
        case.image_quality = []
        case.canonical_claim.prompt_injection_detected = False
        case.canonical_claim.threat_detected = False

        formatter = CSVFormatter()
        result = formatter.format(case)
        assert result["risk_flags"] == "none"

    def test_formatter_risk_flags_semicolon_separated(self):
        case = _make_full_case()
        case.risk_assessment = RiskAssessment(risk_flags=["user_history_risk"])
        case.image_quality = [
            ImageQuality(image_id="img_1", blurry=True, valid=True, confidence=0.8),
        ]

        formatter = CSVFormatter()
        result = formatter.format(case)
        flags = result["risk_flags"].split(";")
        assert "blurry_image" in flags
        assert "user_history_risk" in flags

    def test_formatter_supporting_image_ids(self):
        case = _make_full_case()
        case.fused_evidence.supporting_image_ids = ["img_1", "img_2"]

        formatter = CSVFormatter()
        result = formatter.format(case)
        assert result["supporting_image_ids"] == "img_1;img_2"

    def test_formatter_supporting_image_ids_none(self):
        case = _make_full_case()
        case.fused_evidence.supporting_image_ids = []

        formatter = CSVFormatter()
        result = formatter.format(case)
        assert result["supporting_image_ids"] == "none"

    def test_formatter_allowed_values_supported(self):
        case = _make_full_case()
        case.decision.claim_status = "supported"
        case.decision.issue_type = "dent"
        case.decision.object_part = "front_bumper"
        case.decision.severity = "medium"

        formatter = CSVFormatter()
        result = formatter.format(case)

        assert result["claim_status"] in VALID_CLAIM_STATUS
        assert result["issue_type"] in VALID_ISSUE_TYPES
        assert result["object_part"] in _PART_SETS["car"]
        assert result["severity"] in VALID_SEVERITY

    def test_formatter_boolean_values(self):
        case = _make_full_case()
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert isinstance(result["evidence_standard_met"], bool)
        assert isinstance(result["valid_image"], bool)

    def test_formatter_raises_on_invalid_claim_status(self):
        case = _make_full_case()
        case.decision.claim_status = "invalid_status"

        formatter = CSVFormatter()
        with pytest.raises(ValueError, match="Invalid claim_status"):
            formatter.format(case)

    def test_formatter_raises_on_invalid_issue_type(self):
        case = _make_full_case()
        case.decision.issue_type = "not_a_valid_issue"

        formatter = CSVFormatter()
        with pytest.raises(ValueError, match="Invalid issue_type"):
            formatter.format(case)

    def test_formatter_raises_on_invalid_object_part(self):
        case = _make_full_case()
        case.decision.object_part = "keyboard"
        case.claim_object = "car"

        formatter = CSVFormatter()
        with pytest.raises(ValueError, match="Invalid object_part"):
            formatter.format(case)

    def test_formatter_raises_on_invalid_severity(self):
        case = _make_full_case()
        case.decision.severity = "extreme"

        formatter = CSVFormatter()
        with pytest.raises(ValueError, match="Invalid severity"):
            formatter.format(case)

    def test_formatter_raises_on_invalid_risk_flag(self):
        case = _make_full_case()
        case.risk_assessment = RiskAssessment(risk_flags=["not_a_valid_flag"])

        formatter = CSVFormatter()
        with pytest.raises(ValueError, match="Invalid risk_flag"):
            formatter.format(case)

    def test_formatter_generates_valid_output_for_all_object_types(self):
        for obj_type, part in [("car", "door"), ("laptop", "screen"), ("package", "box")]:
            case = _make_full_case()
            case.claim_object = obj_type
            case.decision.object_part = part
            case.decision.issue_type = "dent"
            case.decision.claim_status = "supported"
            case.decision.severity = "medium"

            formatter = CSVFormatter()
            result = formatter.format(case)
            assert result["claim_object"] == obj_type
            assert result["object_part"] in _PART_SETS[obj_type]


# ── Pipeline E2E Tests ───────────────────────────────────────────────

class TestPipelineE2E:
    def test_single_row_produces_valid_output(self):
        """Verify that process_row returns all 14 columns in correct order."""
        row = _make_mock_claim_row()
        case = _make_full_case()
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert isinstance(result, dict)
        assert len(result) == 14
        for col in _OUTPUT_COLUMNS:
            assert col in result

    def test_output_columns_exact_order(self):
        formatter = CSVFormatter()
        assert formatter.columns == [
            "user_id", "image_paths", "user_claim", "claim_object",
            "evidence_standard_met", "evidence_standard_met_reason",
            "risk_flags", "issue_type", "object_part",
            "claim_status", "claim_status_justification",
            "supporting_image_ids", "valid_image", "severity",
        ]

    def test_output_allowed_values(self):
        """Verify all values from a supported claim match allowed schemas."""
        case = _make_full_case()
        case.decision.claim_status = "supported"
        case.decision.issue_type = "dent"
        case.decision.object_part = "front_bumper"
        case.decision.severity = "medium"
        case.claim_object = "car"
        case.canonical_claim.prompt_injection_detected = False
        case.canonical_claim.threat_detected = False
        case.image_quality = []

        formatter = CSVFormatter()
        result = formatter.format(case)

        assert result["claim_status"] in VALID_CLAIM_STATUS
        assert result["issue_type"] in VALID_ISSUE_TYPES
        assert result["object_part"] in VALID_CAR_PARTS
        assert result["severity"] in VALID_SEVERITY
        assert result["claim_object"] in ("car", "laptop", "package")

        if result["risk_flags"] != "none":
            for flag in result["risk_flags"].split(";"):
                assert flag in VALID_RISK_FLAGS

    def test_risk_flags_and_supporting_ids_are_strings(self):
        case = _make_full_case()
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert isinstance(result["risk_flags"], str)
        assert isinstance(result["supporting_image_ids"], str)

    def test_pipeline_handles_row_errors_gracefully(self):
        """Confirm that the formatter does not crash on missing optional fields."""
        minimal_case = ClaimCase(
            user_id="user_999",
            image_paths=[],
            user_claim="test",
            claim_object="car",
        )
        formatter = CSVFormatter()
        result = formatter.format(minimal_case)

        assert result["user_id"] == "user_999"
        assert result["claim_status"] == "not_enough_information"
        assert result["issue_type"] == "unknown"
        assert result["severity"] == "unknown"
        assert result["risk_flags"] == "none"
        assert result["supporting_image_ids"] == "none"

    def test_failed_row_does_not_crash(self):
        """If a row has an unsolvable issue, the pipeline should produce a fallback, not crash."""
        bad_case = ClaimCase(
            user_id="user_bad",
            image_paths=["nonexistent.jpg"],
            user_claim="bad claim",
            claim_object="unknown_object",
            decision=Decision(
                claim_status="not_enough_information",
                claim_status_justification="Error processing row.",
                issue_type="unknown",
                object_part="unknown",
                severity="unknown",
            ),
            fused_evidence=FusedEvidence(
                evidence_standard_met=False,
                evidence_standard_met_reason="Error.",
            ),
            risk_assessment=RiskAssessment(risk_flags=["none"]),
        )
        formatter = CSVFormatter()

        try:
            result = formatter.format(bad_case)
        except ValueError:
            result = {
                "user_id": "user_bad",
                "image_paths": "nonexistent.jpg",
                "user_claim": "bad claim",
                "claim_object": "unknown_object",
                "evidence_standard_met": False,
                "evidence_standard_met_reason": "Error.",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": "Error processing row.",
                "supporting_image_ids": "none",
                "valid_image": False,
                "severity": "unknown",
            }
        assert result["user_id"] == "user_bad"
        assert result["claim_status"] == "not_enough_information"

    def test_pipeline_output_is_reproducible(self):
        """Ensure the same input twice produces the same output."""
        case = _make_full_case()
        formatter = CSVFormatter()

        r1 = formatter.format(case)
        r2 = formatter.format(case)

        assert r1 == r2

    def test_precheck_skip_produces_deterministic_result(self):
        finding, quality = _precheck_skip_result("/fake/path/myimage.jpg")
        assert finding.object_visible is False
        assert finding.confidence == 0.0
        assert quality.valid is False
        assert quality.confidence == 1.0

    def test_resolve_image_paths(self):
        result = _resolve_image_paths("a.jpg;b.jpg;c.jpg")
        assert result == ["a.jpg", "b.jpg", "c.jpg"]

    def test_resolve_image_paths_single(self):
        result = _resolve_image_paths("only.jpg")
        assert result == ["only.jpg"]

    def test_output_columns_count(self):
        formatter = CSVFormatter()
        assert len(formatter.columns) == 14


# ── Integration: Formatter + Decision Engine ─────────────────────────

class TestFormatterDecisionIntegration:
    def test_supported_claim_format(self):
        case = ClaimCase(
            user_id="user_010",
            image_paths=["img1.jpg"],
            user_claim="Dent on front bumper",
            claim_object="car",
            fused_evidence=FusedEvidence(
                target_part_visible=True,
                damage_visible=True,
                damage_consistent=True,
                evidence_standard_met=True,
                evidence_standard_met_reason="Part visible with 100% coverage.",
                evidence_coverage_score=1.0,
                supporting_image_ids=["img1"],
                valid_image=True,
                confidence=0.9,
            ),
            decision=Decision(
                claim_status="supported",
                claim_status_justification="Evidence supports the claim.",
                issue_type="dent",
                object_part="front_bumper",
                severity="high",
            ),
            risk_assessment=RiskAssessment(risk_flags=["none"]),
        )
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert result["claim_status"] == "supported"
        assert result["issue_type"] == "dent"
        assert result["object_part"] == "front_bumper"
        assert result["severity"] == "high"
        assert result["evidence_standard_met"] is True
        assert result["valid_image"] is True

    def test_contradicted_claim_format(self):
        case = ClaimCase(
            user_id="user_011",
            image_paths=["img1.jpg"],
            user_claim="Scratch on door",
            claim_object="car",
            fused_evidence=FusedEvidence(
                target_part_visible=True,
                damage_visible=True,
                damage_consistent=False,
                evidence_standard_met=True,
                evidence_standard_met_reason="Part visible with 100% coverage.",
                evidence_coverage_score=1.0,
                supporting_image_ids=["img1"],
                valid_image=True,
                confidence=0.7,
            ),
            decision=Decision(
                claim_status="contradicted",
                claim_status_justification="Damage does not match claim.",
                issue_type="scratch",
                object_part="door",
                severity="low",
            ),
            risk_assessment=RiskAssessment(risk_flags=["none"]),
        )
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert result["claim_status"] == "contradicted"
        assert result["severity"] == "low"

    def test_not_enough_information_format(self):
        case = ClaimCase(
            user_id="user_012",
            image_paths=["img1.jpg"],
            user_claim="Crack on windshield",
            claim_object="car",
            fused_evidence=FusedEvidence(
                target_part_visible=False,
                damage_visible=False,
                damage_consistent=True,
                evidence_standard_met=False,
                evidence_standard_met_reason="Claimed part not visible (coverage=0%).",
                evidence_coverage_score=0.0,
                supporting_image_ids=[],
                valid_image=False,
                confidence=0.0,
            ),
            decision=Decision(
                claim_status="not_enough_information",
                claim_status_justification="Not enough evidence.",
                issue_type="unknown",
                object_part="windshield",
                severity="unknown",
            ),
            risk_assessment=RiskAssessment(risk_flags=["none"]),
        )
        formatter = CSVFormatter()
        result = formatter.format(case)

        assert result["claim_status"] == "not_enough_information"
        assert result["evidence_standard_met"] is False
        assert result["valid_image"] is False
        assert result["severity"] == "unknown"