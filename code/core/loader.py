import csv
import os

from code.core.config import (
    CLAIMS_CSV, SAMPLE_CLAIMS_CSV,
    USER_HISTORY_CSV, EVIDENCE_REQUIREMENTS_CSV,
)


class DataLoader:
    def __init__(self):
        self.claims = list(self._read_csv(CLAIMS_CSV))
        self.sample_claims = list(self._read_csv(SAMPLE_CLAIMS_CSV))
        self.user_history = list(self._read_csv(USER_HISTORY_CSV))
        self.evidence_requirements = list(self._read_csv(EVIDENCE_REQUIREMENTS_CSV))

    @staticmethod
    def _read_csv(path):
        if not os.path.exists(path):
            return iter([])
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def get_user_history(self, user_id):
        for row in self.user_history:
            if row.get("user_id") == user_id:
                return row
        return None

    def get_evidence_requirement(self, claim_object, claimed_issue):
        for row in self.evidence_requirements:
            if row.get("object_type") == claim_object and row.get("issue_type") == claimed_issue:
                return row
        return None
