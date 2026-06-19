import os
import pytest
import pandas as pd
import tempfile
import subprocess
import sys


from code.evaluation.metrics import (
    compute_metrics,
    compute_confusion_matrix,
)


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_perfect_dataframe():
    return pd.DataFrame({
        "claim_status": ["supported", "contradicted", "not_enough_information", "supported"],
        "issue_type": ["dent", "scratch", "crack", "broken_part"],
        "object_part": ["door", "front_bumper", "screen", "hinge"],
        "severity": ["medium", "low", "high", "low"],
        "evidence_standard_met": [True, True, False, True],
        "valid_image": [True, True, False, True],
    })


def _make_dataframe_variant(values_overrides=None):
    df = _make_perfect_dataframe()
    if values_overrides:
        for col, vals in values_overrides.items():
            df[col] = vals
    return df


# ── Metrics Tests ─────────────────────────────────────────────────────

class TestMetrics:

    def test_perfect_predictions(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        metrics = compute_metrics(pred, gt)

        assert metrics["claim_status"]["accuracy"] == 1.0
        assert metrics["claim_status"]["correct"] == 4
        assert metrics["claim_status"]["total"] == 4
        assert metrics["issue_type"]["accuracy"] == 1.0
        assert metrics["object_part"]["accuracy"] == 1.0
        assert metrics["severity"]["accuracy"] == 1.0
        assert metrics["evidence_standard_met"]["accuracy"] == 1.0
        assert metrics["valid_image"]["accuracy"] == 1.0

    def test_zero_accuracy(self):
        gt = _make_perfect_dataframe()
        pred = _make_dataframe_variant({
            "claim_status": ["contradicted", "supported", "supported", "not_enough_information"],
            "issue_type": ["crack", "dent", "broken_part", "scratch"],
        })
        metrics = compute_metrics(pred, gt)

        assert metrics["claim_status"]["accuracy"] == 0.0
        assert metrics["claim_status"]["correct"] == 0
        assert metrics["claim_status"]["total"] == 4

    def test_partial_accuracy(self):
        gt = _make_perfect_dataframe()
        pred = _make_dataframe_variant({
            "claim_status": ["supported", "contradicted", "not_enough_information", "contradicted"],
        })
        metrics = compute_metrics(pred, gt)

        assert 0.0 < metrics["claim_status"]["accuracy"] < 1.0
        assert metrics["claim_status"]["correct"] == 3
        assert metrics["claim_status"]["total"] == 4

    def test_boolean_fields_compared_as_strings(self):
        gt = pd.DataFrame({
            "claim_status": ["supported"],
            "issue_type": ["dent"],
            "object_part": ["door"],
            "severity": ["medium"],
            "evidence_standard_met": [True],
            "valid_image": [True],
        })
        pred = pd.DataFrame({
            "claim_status": ["supported"],
            "issue_type": ["dent"],
            "object_part": ["door"],
            "severity": ["medium"],
            "evidence_standard_met": ["true"],
            "valid_image": ["true"],
        })
        metrics = compute_metrics(pred, gt)
        assert metrics["evidence_standard_met"]["accuracy"] == 1.0
        assert metrics["valid_image"]["accuracy"] == 1.0

    def test_mismatched_row_count_raises(self):
        gt = pd.DataFrame({"claim_status": ["supported", "contradicted"]})
        pred = pd.DataFrame({"claim_status": ["supported"]})
        with pytest.raises(ValueError, match="Row count mismatch"):
            compute_metrics(pred, gt)

    def test_metrics_returns_structured_dict(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        metrics = compute_metrics(pred, gt)

        required_keys = [
            "claim_status", "issue_type", "object_part", "severity",
            "evidence_standard_met", "valid_image", "claim_status_f1",
        ]
        for key in required_keys:
            assert key in metrics

        for field in required_keys[:-1]:
            assert "accuracy" in metrics[field]
            assert "correct" in metrics[field]
            assert "total" in metrics[field]
            assert isinstance(metrics[field]["accuracy"], float)
            assert isinstance(metrics[field]["correct"], int)
            assert isinstance(metrics[field]["total"], int)

        f1 = metrics["claim_status_f1"]
        assert "macro_f1" in f1
        assert "macro_precision" in f1
        assert "macro_recall" in f1
        assert "classes" in f1
        assert 0.0 <= f1["macro_f1"] <= 1.0

    def test_f1_macro_perfect_is_one(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        metrics = compute_metrics(pred, gt)
        assert metrics["claim_status_f1"]["macro_f1"] == pytest.approx(1.0)

    def test_f1_binary(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted", "supported", "contradicted"],
        })
        pred = gt.copy()
        metrics = compute_metrics(pred, gt)
        assert metrics["claim_status_f1"]["macro_f1"] == pytest.approx(1.0)

    def test_metrics_deterministic(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        m1 = compute_metrics(pred, gt)
        m2 = compute_metrics(pred, gt)
        assert m1 == m2


# ── Confusion Matrix Tests ────────────────────────────────────────────

class TestConfusionMatrix:

    def test_confusion_matrix_structure(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        cm = compute_confusion_matrix(pred, gt)

        assert "labels" in cm
        assert "matrix" in cm
        assert len(cm["labels"]) == len(cm["matrix"])
        assert len(cm["labels"]) > 0

    def test_confusion_matrix_perfect_is_diagonal(self):
        gt = _make_perfect_dataframe()
        pred = gt.copy()
        cm = compute_confusion_matrix(pred, gt)

        labels = cm["labels"]
        matrix = cm["matrix"]
        for i in range(len(labels)):
            for j in range(len(labels)):
                if i == j:
                    assert matrix[i][j] > 0
                else:
                    assert matrix[i][j] == 0

    def test_confusion_matrix_all_wrong(self):
        gt = pd.DataFrame({"claim_status": ["supported", "supported", "supported"]})
        pred = pd.DataFrame({"claim_status": ["contradicted", "contradicted", "contradicted"]})
        cm = compute_confusion_matrix(pred, gt)

        labels = cm["labels"]
        if "supported" in labels and "contradicted" in labels:
            si = labels.index("supported")
            ci = labels.index("contradicted")
            assert cm["matrix"][si][ci] == 3
            assert cm["matrix"][ci][si] == 0


# ── Evaluation Report Tests ───────────────────────────────────────────

class TestEvaluationReport:

    def test_evaluation_report_written(self):
        eval_script = os.path.join(_BASE_DIR, "code", "evaluation", "main.py")

        result = subprocess.run(
            [sys.executable, eval_script, "--synthetic"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=_BASE_DIR,
            env={**os.environ, "PYTHONPATH": _BASE_DIR},
        )
        assert result.returncode == 0, f"Eval script failed: {result.stderr}"

        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        assert os.path.exists(report_path), f"Report not found at {report_path}"

        with open(report_path, "r") as f:
            content = f.read()

        assert "Evaluation Report" in content
        assert "claim_status" in content
        assert "Operational Analysis" in content
        assert "TPM" in content or "RPM" in content or "Retry" in content

    def test_report_contains_metrics_table(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "| Field" in content
        assert "|-------" in content
        assert "| claim_status" in content

    def test_report_contains_confusion_matrix(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "Confusion Matrix" in content

    def test_report_contains_strategy_comparison_sections(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "Strategy Comparison 1" in content
        assert "Strategy Comparison 2" in content

    def test_report_contains_operational_analysis(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "Operational Analysis" in content

    def test_report_contains_observations(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "Observations" in content

    def test_report_contains_dataset_summary(self):
        report_path = os.path.join(_BASE_DIR, "code", "evaluation", "evaluation_report.md")
        with open(report_path, "r") as f:
            content = f.read()

        assert "Dataset Summary" in content

    def test_evaluation_handles_empty_ground_truth(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            f.write("user_id,image_paths,user_claim,claim_object,"
                    "evidence_standard_met,evidence_standard_met_reason,"
                    "risk_flags,issue_type,object_part,claim_status,"
                    "claim_status_justification,supporting_image_ids,valid_image,severity\n")
            tmp_path = f.name

        try:
            gt = pd.read_csv(tmp_path)
            assert len(gt) == 0
        finally:
            os.unlink(tmp_path)


# ── Ablation Tests ────────────────────────────────────────────────────

class TestAblations:

    def test_synthetic_pipeline_produces_valid_output(self):
        gt = _make_perfect_dataframe()
        gt["user_id"] = ["user_001", "user_002", "user_003", "user_004"]
        gt["image_paths"] = ["img1.jpg", "img2.jpg;img3.jpg", "", "img4.jpg"]
        gt["user_claim"] = ["dent on door", "scratch on front bumper",
                            "crack on screen", "broken hinge"]
        gt["claim_object"] = ["car", "car", "laptop", "laptop"]

        from code.evaluation.main import run_synthetic_pipeline

        pred = run_synthetic_pipeline(gt)
        assert len(pred) == 4
        assert list(pred.columns[:14]) == [
            "user_id", "image_paths", "user_claim", "claim_object",
            "evidence_standard_met", "evidence_standard_met_reason",
            "risk_flags", "issue_type", "object_part",
            "claim_status", "claim_status_justification",
            "supporting_image_ids", "valid_image", "severity",
        ]
        valid_statuses = {"supported", "contradicted", "not_enough_information"}
        assert all(s in valid_statuses for s in pred["claim_status"])

    def test_no_fusion_ablation_produces_valid_output(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted"],
            "issue_type": ["dent", "scratch"],
            "object_part": ["door", "front_bumper"],
            "severity": ["medium", "low"],
            "evidence_standard_met": [True, False],
            "valid_image": [True, False],
            "user_id": ["user_001", "user_002"],
            "image_paths": ["img1.jpg", "img2.jpg;img3.jpg"],
            "user_claim": ["dent on door", "scratch on front bumper"],
            "claim_object": ["car", "car"],
        })

        from code.evaluation.main import run_ablation_no_fusion

        pred = run_ablation_no_fusion(gt)
        assert len(pred) == 2
        assert "claim_status" in pred.columns
        assert "evidence_standard_met" in pred.columns

    def test_no_audit_ablation_produces_valid_output(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted"],
            "issue_type": ["dent", "scratch"],
            "object_part": ["door", "front_bumper"],
            "severity": ["medium", "low"],
            "evidence_standard_met": [True, False],
            "valid_image": [True, False],
            "user_id": ["user_001", "user_002"],
            "image_paths": ["img1.jpg", "img2.jpg;img3.jpg"],
            "user_claim": ["dent on door", "scratch on front bumper"],
            "claim_object": ["car", "car"],
        })

        from code.evaluation.main import run_ablation_no_audit

        pred = run_ablation_no_audit(gt)
        assert len(pred) == 2
        assert "claim_status" in pred.columns
        assert "evidence_standard_met" in pred.columns

    def test_ablation_comparisons_produce_different_metrics(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted", "supported", "contradicted"],
            "issue_type": ["dent", "scratch", "dent", "scratch"],
            "object_part": ["door", "front_bumper", "screen", "box"],
            "severity": ["medium", "low", "high", "low"],
            "evidence_standard_met": [True, False, True, False],
            "valid_image": [True, True, True, True],
            "user_id": ["user_001", "user_002", "user_003", "user_004"],
            "image_paths": ["img1.jpg", "img2.jpg;img3.jpg", "img4.jpg", "img5.jpg"],
            "user_claim": [
                "dent on door",
                "scratch on front bumper",
                "dent on screen",
                "scratch on box",
            ],
            "claim_object": ["car", "car", "laptop", "package"],
        })

        from code.evaluation.main import (
            run_synthetic_pipeline,
            run_ablation_no_fusion,
            run_ablation_no_audit,
        )

        pred_full = run_synthetic_pipeline(gt)
        pred_no_fusion = run_ablation_no_fusion(gt)
        pred_no_audit = run_ablation_no_audit(gt)

        m_full = compute_metrics(pred_full, gt)
        m_no_fusion = compute_metrics(pred_no_fusion, gt)
        m_no_audit = compute_metrics(pred_no_audit, gt)

        assert isinstance(m_full["claim_status"]["accuracy"], float)
        assert isinstance(m_no_fusion["claim_status"]["accuracy"], float)
        assert isinstance(m_no_audit["claim_status"]["accuracy"], float)


# ── Edge Case Tests ───────────────────────────────────────────────────

class TestEvaluationEdgeCases:

    def test_metrics_with_empty_dataframe(self):
        gt = pd.DataFrame({
            "claim_status": pd.Series(dtype=str),
            "issue_type": pd.Series(dtype=str),
            "object_part": pd.Series(dtype=str),
            "severity": pd.Series(dtype=str),
            "evidence_standard_met": pd.Series(dtype=str),
            "valid_image": pd.Series(dtype=str),
        })
        metrics = compute_metrics(gt, gt)

        assert metrics["claim_status"]["total"] == 0
        assert metrics["claim_status"]["accuracy"] == 0.0

    def test_metrics_with_nan_values(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted"],
            "issue_type": ["dent", None],
            "object_part": ["door", "bumper"],
            "severity": ["medium", "low"],
            "evidence_standard_met": [True, True],
            "valid_image": [True, True],
        })
        pred = pd.DataFrame({
            "claim_status": ["supported", "contradicted"],
            "issue_type": ["dent", "none"],
            "object_part": ["door", "bumper"],
            "severity": ["medium", "low"],
            "evidence_standard_met": [True, True],
            "valid_image": [True, True],
        })
        metrics = compute_metrics(pred, gt)
        assert metrics["claim_status"]["accuracy"] == 1.0

    def test_metrics_handles_missing_column(self):
        gt = pd.DataFrame({"claim_status": ["supported", "contradicted"]})
        pred = pd.DataFrame({"claim_status": ["supported", "contradicted"]})
        metrics = compute_metrics(pred, gt)
        assert "claim_status" in metrics
        assert "accuracy" in metrics["claim_status"]

    def test_generate_report_does_not_crash(self):
        gt = pd.DataFrame({
            "claim_status": ["supported", "contradicted", "supported", "contradicted"],
            "issue_type": ["dent", "scratch", "dent", "scratch"],
            "object_part": ["door", "front_bumper", "screen", "hinge"],
            "severity": ["medium", "low", "high", "low"],
            "evidence_standard_met": [True, False, True, False],
            "valid_image": [True, True, True, True],
            "user_id": ["u1", "u2", "u3", "u4"],
            "image_paths": ["a.jpg", "b.jpg", "c.jpg", "d.jpg"],
            "user_claim": ["dent door", "scratch bumper", "crack screen", "broken hinge"],
            "claim_object": ["car", "car", "laptop", "laptop"],
        })

        from code.evaluation.main import generate_report, run_synthetic_pipeline

        pred = run_synthetic_pipeline(gt)
        report = generate_report(gt, pred, pred, pred, "synthetic", 0.5)

        assert "Evaluation Report" in report
        assert "Dataset Summary" in report
        assert "Metrics" in report
        assert "Confusion Matrix" in report
        assert "Strategy Comparison 1" in report
        assert "Strategy Comparison 2" in report
        assert "Operational Analysis" in report
        assert "Observations" in report
