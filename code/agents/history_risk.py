from code.core.loader import DataLoader
from code.core.models import RiskAssessment


class HistoryRiskAgent:
    def __init__(self):
        self.loader = DataLoader()

    def assess_risk(self, user_id: str) -> RiskAssessment:
        row = self.loader.get_user_history(user_id)
        if not row:
            return RiskAssessment(risk_flags=["none"])

        flags: set[str] = set()
        rejected = int(row.get("rejected_claim", 0) or 0)
        manual_review = int(row.get("manual_review_claim", 0) or 0)
        history_flags = str(row.get("history_flags", "")).strip()

        if rejected >= 2 or history_flags not in ("", "none", "nan", "None"):
            flags.add("user_history_risk")
        if manual_review >= 1:
            flags.add("manual_review_required")

        flag_list = sorted(flags) if flags else ["none"]
        return RiskAssessment(
            risk_flags=flag_list,
            user_history_risk=bool(flags),
        )
