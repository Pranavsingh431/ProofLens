from typing import Optional, List
from pydantic import BaseModel


class CanonicalClaim(BaseModel):
    claimed_issue: str = "unknown"
    claimed_part: str = "unknown"
    keywords: List[str] = []
    language: str = "en"
    multi_part: bool = False
    secondary_issue: Optional[str] = None
    secondary_part: Optional[str] = None
    prompt_injection_detected: bool = False
    threat_detected: bool = False
    confidence: float = 1.0


class EvidenceRequirement(BaseModel):
    object_type: str
    issue_type: str
    minimum_image_evidence: str
    applies_to: str


class ImageFindings(BaseModel):
    image_id: str = ""
    object_visible: bool = False
    visible_parts: List[str] = []
    issue_detected: Optional[str] = None
    issue_severity: str = "unknown"
    confidence: float = 0.0


class ImageQuality(BaseModel):
    image_id: str = ""
    blurry: bool = False
    cropped_or_obstructed: bool = False
    low_light_or_glare: bool = False
    wrong_angle: bool = False
    wrong_object: bool = False
    possible_manipulation: bool = False
    non_original_image: bool = False
    text_instruction_present: bool = False
    valid: bool = True
    confidence: float = 1.0


class FusedEvidence(BaseModel):
    target_part_visible: bool = False
    damage_visible: bool = False
    damage_consistent: bool = True
    evidence_standard_met: bool = False
    evidence_standard_met_reason: str = ""
    evidence_coverage_score: float = 0.0
    supporting_image_ids: List[str] = []
    valid_image: bool = False
    confidence: float = 0.0


class RiskAssessment(BaseModel):
    risk_flags: List[str] = []
    user_history_risk: bool = False


class Decision(BaseModel):
    claim_status: str = "not_enough_information"
    claim_status_justification: str = ""
    issue_type: str = "unknown"
    object_part: str = "unknown"
    severity: str = "unknown"


class AuditResult(BaseModel):
    passed: bool = True
    inconsistencies: List[str] = []
    rerun_agents: List[str] = []


class ClaimCase(BaseModel):
    user_id: str = ""
    image_paths: List[str] = []
    user_claim: str = ""
    claim_object: str = ""
    prompt_injection: bool = False
    threat_language: bool = False
    detected_language: str = "en"
    canonical_claim: Optional[CanonicalClaim] = None
    evidence_requirement: Optional[EvidenceRequirement] = None
    image_findings: List[ImageFindings] = []
    image_quality: List[ImageQuality] = []
    fused_evidence: Optional[FusedEvidence] = None
    risk_assessment: Optional[RiskAssessment] = None
    decision: Optional[Decision] = None
    audit_result: Optional[AuditResult] = None
