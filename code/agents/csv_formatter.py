from code.core.models import ClaimCase
from code.core.config import (
    VALID_OBJECT_TYPES, VALID_CLAIM_STATUS, VALID_ISSUE_TYPES,
    VALID_CAR_PARTS, VALID_LAPTOP_PARTS, VALID_PACKAGE_PARTS,
    VALID_RISK_FLAGS, VALID_SEVERITY,
)

_OUTPUT_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason",
    "risk_flags", "issue_type", "object_part",
    "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity",
]

_PART_SETS = {
    "car": VALID_CAR_PARTS,
    "laptop": VALID_LAPTOP_PARTS,
    "package": VALID_PACKAGE_PARTS,
}


class CSVFormatter:
    def format(self, case: ClaimCase) -> dict:
        risk_flags_str = self._build_risk_flags(case)
        supporting_ids_str = self._build_supporting_ids(case)

        result = {
            "user_id": case.user_id,
            "image_paths": ";".join(case.image_paths),
            "user_claim": case.user_claim,
            "claim_object": case.claim_object,
            "evidence_standard_met": case.fused_evidence.evidence_standard_met if case.fused_evidence else False,
            "evidence_standard_met_reason": case.fused_evidence.evidence_standard_met_reason if case.fused_evidence else "",
            "risk_flags": risk_flags_str,
            "issue_type": case.decision.issue_type if case.decision else "unknown",
            "object_part": case.decision.object_part if case.decision else "unknown",
            "claim_status": case.decision.claim_status if case.decision else "not_enough_information",
            "claim_status_justification": case.decision.claim_status_justification if case.decision else "",
            "supporting_image_ids": supporting_ids_str,
            "valid_image": case.fused_evidence.valid_image if case.fused_evidence else False,
            "severity": case.decision.severity if case.decision else "unknown",
        }

        self._validate(result)
        return result

    def _build_risk_flags(self, case: ClaimCase) -> str:
        flags: set[str] = set()

        if case.risk_assessment:
            for f in case.risk_assessment.risk_flags:
                if f != "none":
                    flags.add(f)

        for q in case.image_quality:
            if q.blurry:
                flags.add("blurry_image")
            if q.cropped_or_obstructed:
                flags.add("cropped_or_obstructed")
            if q.low_light_or_glare:
                flags.add("low_light_or_glare")
            if q.wrong_angle:
                flags.add("wrong_angle")
            if q.wrong_object:
                flags.add("wrong_object")
            if q.possible_manipulation:
                flags.add("possible_manipulation")
            if q.non_original_image:
                flags.add("non_original_image")
            if q.text_instruction_present:
                flags.add("text_instruction_present")

        if case.canonical_claim:
            if case.canonical_claim.prompt_injection_detected:
                flags.add("text_instruction_present")
            if case.canonical_claim.threat_detected:
                flags.add("manual_review_required")

        if case.fused_evidence and not case.fused_evidence.damage_visible and case.fused_evidence.target_part_visible:
            flags.add("damage_not_visible")

        if not flags:
            return "none"

        return ";".join(sorted(flags))

    def _build_supporting_ids(self, case: ClaimCase) -> str:
        if not case.fused_evidence or not case.fused_evidence.supporting_image_ids:
            return "none"
        return ";".join(case.fused_evidence.supporting_image_ids)

    def _validate(self, row: dict) -> None:
        if row["claim_object"] not in VALID_OBJECT_TYPES:
            raise ValueError(f"Invalid claim_object: {row['claim_object']}")

        if row["claim_status"] not in VALID_CLAIM_STATUS:
            raise ValueError(f"Invalid claim_status: {row['claim_status']}")

        if row["issue_type"] not in VALID_ISSUE_TYPES:
            raise ValueError(f"Invalid issue_type: {row['issue_type']}")

        valid_parts = _PART_SETS.get(row["claim_object"], {"unknown"})
        if row["object_part"] not in valid_parts:
            raise ValueError(
                f"Invalid object_part '{row['object_part']}' for claim_object '{row['claim_object']}'"
            )

        if row["severity"] not in VALID_SEVERITY:
            raise ValueError(f"Invalid severity: {row['severity']}")

        if row["risk_flags"] != "none":
            for flag in row["risk_flags"].split(";"):
                if flag not in VALID_RISK_FLAGS:
                    raise ValueError(f"Invalid risk_flag: {flag}")

    @property
    def columns(self) -> list:
        return list(_OUTPUT_COLUMNS)
