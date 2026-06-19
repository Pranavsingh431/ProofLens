import csv
import os
from pathlib import Path

from code.core.config import (
    DATASET_DIR,
    CLAIMS_CSV,
    SAMPLE_CLAIMS_CSV,
    USER_HISTORY_CSV,
    EVIDENCE_REQUIREMENTS_CSV,
)


class DataLoader:
    def __init__(self):
        self._claims = None
        self._sample_claims = None
        self._user_history = None
        self._evidence_requirements = None

    @property
    def claims(self):
        if self._claims is None:
            self._claims = self._read_csv(CLAIMS_CSV)
        return self._claims

    @property
    def sample_claims(self):
        if self._sample_claims is None:
            self._sample_claims = self._read_csv(SAMPLE_CLAIMS_CSV)
        return self._sample_claims

    @property
    def user_history(self):
        if self._user_history is None:
            self._user_history = self._read_csv(USER_HISTORY_CSV)
        return self._user_history

    @property
    def evidence_requirements(self):
        if self._evidence_requirements is None:
            self._evidence_requirements = self._read_csv(EVIDENCE_REQUIREMENTS_CSV)
        return self._evidence_requirements

    @staticmethod
    def _read_csv(filepath):
        rows = []
        if not filepath.exists():
            return rows
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    def resolve_image_paths(self, image_paths_str):
        paths = []
        for p in image_paths_str.split(";"):
            p = p.strip()
            if not p:
                continue
            full = DATASET_DIR / p
            if full.exists():
                paths.append(str(full))
            else:
                paths.append(p)
        return paths

    def validate_image_paths(self):
        missing = []
        for row in self.claims:
            for p in row.get("image_paths", "").split(";"):
                p = p.strip()
                if not p:
                    continue
                full = DATASET_DIR / p
                if not full.exists():
                    missing.append(str(full))
        for row in self.sample_claims:
            for p in row.get("image_paths", "").split(";"):
                p = p.strip()
                if not p:
                    continue
                full = DATASET_DIR / p
                if not full.exists():
                    missing.append(str(full))
        return missing

    def get_user_history(self, user_id):
        for row in self.user_history:
            if row.get("user_id") == user_id:
                return row
        return None

    def get_evidence_requirement(self, object_type, issue_type):
        for row in self.evidence_requirements:
            if row.get("object_type") == object_type and row.get("issue_type") == issue_type:
                return row
        return None
