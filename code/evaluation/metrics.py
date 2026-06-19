import pandas as pd


def compute_metrics(predictions: pd.DataFrame, ground_truth: pd.DataFrame) -> dict:
    if len(predictions) != len(ground_truth):
        raise ValueError(
            f"Row count mismatch: predictions={len(predictions)}, ground_truth={len(ground_truth)}"
        )

    results = {}

    comparable_fields = [
        "claim_status",
        "issue_type",
        "object_part",
        "severity",
        "evidence_standard_met",
        "valid_image",
    ]

    for field in comparable_fields:
        if field not in predictions.columns or field not in ground_truth.columns:
            results[field] = {"accuracy": 0.0, "correct": 0, "total": 0, "reason": "missing_column"}
            continue

        pred = predictions[field].astype(str).str.strip().str.lower()
        true = ground_truth[field].astype(str).str.strip().str.lower()

        match = pred == true
        n_correct = int(match.sum())
        n_total = len(true)
        accuracy = (n_correct / n_total) if n_total > 0 else 0.0

        results[field] = {
            "accuracy": round(accuracy, 4),
            "correct": n_correct,
            "total": n_total,
        }

    claim_status_f1 = _compute_f1(
        ground_truth.get("claim_status", pd.Series(dtype=str)),
        predictions.get("claim_status", pd.Series(dtype=str)),
    )
    results["claim_status_f1"] = claim_status_f1

    return results


def _compute_f1(ground_truth: pd.Series, predictions: pd.Series) -> dict:
    true = ground_truth.astype(str).str.strip().str.lower()
    pred = predictions.astype(str).str.strip().str.lower()

    classes = sorted(set(true) | set(pred))
    class_results = {}
    macro_precision = 0.0
    macro_recall = 0.0
    macro_f1 = 0.0
    n_classes = 0

    for cls in classes:
        tp = int(((true == cls) & (pred == cls)).sum())
        fp = int(((true != cls) & (pred == cls)).sum())
        fn = int(((true == cls) & (pred != cls)).sum())

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1_val = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        class_results[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1_val, 4),
            "support": int((true == cls).sum()),
        }
        macro_precision += precision
        macro_recall += recall
        macro_f1 += f1_val
        n_classes += 1

    if n_classes > 0:
        macro_precision /= n_classes
        macro_recall /= n_classes
        macro_f1 /= n_classes

    return {
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "classes": class_results,
    }


def compute_confusion_matrix(predictions: pd.DataFrame, ground_truth: pd.DataFrame) -> dict:
    true = ground_truth["claim_status"].astype(str).str.strip().str.lower()
    pred = predictions["claim_status"].astype(str).str.strip().str.lower()

    labels = sorted(set(true) | set(pred))
    label_index = {label: i for i, label in enumerate(labels)}
    n = len(labels)
    matrix = [[0] * n for _ in range(n)]

    for t, p in zip(true, pred):
        i = label_index[t]
        j = label_index[p]
        matrix[i][j] += 1

    return {"labels": labels, "matrix": matrix}
