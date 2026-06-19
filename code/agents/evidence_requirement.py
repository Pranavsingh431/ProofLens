from code.core.loader import DataLoader
from code.core.models import EvidenceRequirement


class EvidenceRequirementAgent:
    def __init__(self):
        self.loader = DataLoader()

    def lookup(self, claim_object: str, claimed_issue: str) -> EvidenceRequirement:
        row = self.loader.get_evidence_requirement(claim_object, claimed_issue)
        if row:
            return EvidenceRequirement(
                object_type=row["object_type"],
                issue_type=row["issue_type"],
                minimum_image_evidence=row["minimum_image_evidence"],
                applies_to=row["applies_to"],
            )

        for r in self.loader.evidence_requirements:
            if r["object_type"] == claim_object:
                if claimed_issue.lower() in r["applies_to"].lower():
                    return EvidenceRequirement(
                        object_type=r["object_type"],
                        issue_type=r["issue_type"],
                        minimum_image_evidence=r["minimum_image_evidence"],
                        applies_to=r["applies_to"],
                    )

        return EvidenceRequirement(
            object_type=claim_object,
            issue_type=claimed_issue,
            minimum_image_evidence="Claimed part visible with damage evidence",
            applies_to=claimed_issue,
        )
