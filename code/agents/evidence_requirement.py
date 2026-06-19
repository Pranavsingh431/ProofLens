from code.core.models import EvidenceRequirement
from code.core.loader import DataLoader

_loader: DataLoader = None


def _get_loader() -> DataLoader:
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader


class EvidenceRequirementAgent:
    def __init__(self):
        self._loader = _get_loader()

    def lookup(self, object_type: str, issue_type: str) -> EvidenceRequirement:
        # Exact match
        row = self._loader.get_evidence_requirement(object_type, issue_type)
        if row:
            return EvidenceRequirement(
                object_type=row["object_type"],
                issue_type=row["issue_type"],
                minimum_image_evidence=row["minimum_image_evidence"],
                applies_to=row.get("applies_to", ""),
            )

        # Fuzzy fallback — first row matching the object type
        for r in self._loader.evidence_requirements:
            if r.get("object_type") == object_type:
                return EvidenceRequirement(
                    object_type=r["object_type"],
                    issue_type=r["issue_type"],
                    minimum_image_evidence=r["minimum_image_evidence"],
                    applies_to=r.get("applies_to", "general"),
                )

        # Last-resort generic
        return EvidenceRequirement(
            object_type=object_type,
            issue_type=issue_type,
            minimum_image_evidence="at_least_one_image_showing_damage",
            applies_to="general",
        )
