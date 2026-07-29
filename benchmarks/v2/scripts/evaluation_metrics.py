from __future__ import annotations

import math
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_curve, auc, confusion_matrix as sk_confusion_matrix,
    matthews_corrcoef, balanced_accuracy_score, precision_recall_curve
)


class EvaluationMetrics:
    def __init__(
        self,
        y_true: List[int],
        y_pred: List[int],
        y_scores: Optional[List[float]] = None,
        categories: Optional[List[str]] = None,
    ):
        self.y_true = np.array(y_true, dtype=int)
        self.y_pred = np.array(y_pred, dtype=int)
        self.y_scores = np.array(y_scores) if y_scores is not None else None
        self.categories = categories or ["negative", "positive"]

        if len(self.y_true) != len(self.y_pred):
            raise ValueError("y_true and y_pred must have the same length")
        if self.y_scores is not None and len(self.y_scores) != len(self.y_true):
            raise ValueError("y_scores length must match y_true")

        self._metrics: Dict[str, float] = {}
        self._per_category: Dict[str, Dict[str, float]] = {}
        self._confusion_matrix: List[List[int]] = [[0, 0], [0, 0]]
        self._compute()

    def _compute(self) -> None:
        n = len(self.y_true)
        if n == 0:
            self._metrics = {k: float("nan") for k in
                             ["tp", "fp", "fn", "tn", "accuracy", "precision",
                              "recall", "f1", "fpr", "fnr", "mcc", "balanced_accuracy"]}
            return

        tp = int(np.sum((self.y_pred == 1) & (self.y_true == 1)))
        fp = int(np.sum((self.y_pred == 1) & (self.y_true == 0)))
        fn = int(np.sum((self.y_pred == 0) & (self.y_true == 1)))
        tn = int(np.sum((self.y_pred == 0) & (self.y_true == 0)))

        self._confusion_matrix = [[int(tn), int(fp)], [int(fn), int(tp)]]

        accuracy = float(accuracy_score(self.y_true, self.y_pred))
        precision = float(precision_score(self.y_true, self.y_pred, zero_division=0))
        recall = float(recall_score(self.y_true, self.y_pred, zero_division=0))
        f1 = float(f1_score(self.y_true, self.y_pred, zero_division=0))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        mcc = float(matthews_corrcoef(self.y_true, self.y_pred))
        bal_acc = float(balanced_accuracy_score(self.y_true, self.y_pred))

        self._metrics = {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fpr": fpr,
            "fnr": fnr,
            "mcc": mcc,
            "balanced_accuracy": bal_acc,
        }

        scu = int(np.sum(self.y_true == 1))
        if scu > 0:
            self._metrics["num_scams"] = scu
        nlu = int(np.sum(self.y_true == 0))
        if nlu > 0:
            self._metrics["num_legitimate"] = nlu

        if self.y_scores is not None:
            try:
                fpr_roc, tpr_roc, _ = roc_curve(self.y_true, self.y_scores)
                self._metrics["auc"] = float(auc(fpr_roc, tpr_roc))
                self._roc_curve: Optional[Dict] = {
                    "fpr": fpr_roc.tolist(),
                    "tpr": tpr_roc.tolist(),
                }
            except Exception:
                self._metrics["auc"] = float("nan")
                self._roc_curve = None
            try:
                prec_pr, rec_pr, _ = precision_recall_curve(self.y_true, self.y_scores)
                self._pr_curve: Optional[Dict] = {
                    "precision": prec_pr.tolist(),
                    "recall": rec_pr.tolist(),
                }
            except Exception:
                self._pr_curve = None
        else:
            self._metrics["auc"] = float("nan")
            self._roc_curve = None
            self._pr_curve = None

    def per_category_metrics(
        self, y_true: List[int], y_pred: List[int], categories: List[str]
    ) -> Dict[str, Dict[str, float]]:
        result: Dict[str, Dict[str, float]] = {}
        cat_array = np.array(categories)
        unique_cats = np.unique(cat_array)

        y_true_arr = np.array(y_true, dtype=int)
        y_pred_arr = np.array(y_pred, dtype=int)

        for cat in unique_cats:
            mask = cat_array == cat
            if np.sum(mask) == 0:
                continue
            sub_true = y_true_arr[mask]
            sub_pred = y_pred_arr[mask]

            sub_metric = EvaluationMetrics(
                y_true=sub_true.tolist(),
                y_pred=sub_pred.tolist(),
                y_scores=None,
                categories=[cat, "other"]
            )
            result[str(cat)] = sub_metric.to_dict()

        return result

    def confusion_matrix(self) -> List[List[int]]:
        return self._confusion_matrix

    def classification_report(self) -> str:
        lines = ["Classification Report", "=" * 60]
        lines.append(f"{'':20s} {'precision':>10s} {'recall':>10s} {'f1':>10s} {'support':>10s}")
        lines.append("-" * 60)

        for i, label in enumerate(self.categories):
            if i == 0:
                tp_fmt = self._metrics["tn"]
                fn_fmt = self._metrics["fp"]
            else:
                tp_fmt = self._metrics["tp"]
                fn_fmt = self._metrics["fn"]

            support = tp_fmt + fn_fmt
            prec = self._metrics["precision"] if i == 1 else 1 - self._metrics.get("fpr", 0)
            rec = self._metrics["recall"] if i == 1 else 1 - self._metrics.get("fnr", 0)
            f1_v = self._metrics["f1"] if i == 1 else (
                2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            )

            lines.append(f"{label:20s} {prec:10.4f} {rec:10.4f} {f1_v:10.4f} {support:10d}")

        lines.append("-" * 60)
        lines.append(f"{'accuracy':20s} {self._metrics['accuracy']:10.4f} {len(self.y_true):>10d}")
        lines.append(f"{'macro avg':20s} {self._metrics['precision']:10.4f} {self._metrics['recall']:10.4f} {self._metrics['f1']:10.4f} {len(self.y_true):>10d}")
        lines.append(f"{'weighted avg':20s} {self._metrics['precision']:10.4f} {self._metrics['recall']:10.4f} {self._metrics['f1']:10.4f} {len(self.y_true):>10d}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        d.update(self._metrics)
        d["confusion_matrix"] = self._confusion_matrix
        if hasattr(self, "_roc_curve") and self._roc_curve is not None:
            d["roc_curve"] = self._roc_curve
        if hasattr(self, "_pr_curve") and self._pr_curve is not None:
            d["pr_curve"] = self._pr_curve
        return d

    def summary(self) -> str:
        lines = ["Evaluation Summary", "=" * 50]
        lines.append(f"  Accuracy:          {self._metrics.get('accuracy', 'N/A'):>10.4f}")
        lines.append(f"  Precision:         {self._metrics.get('precision', 'N/A'):>10.4f}")
        lines.append(f"  Recall:            {self._metrics.get('recall', 'N/A'):>10.4f}")
        lines.append(f"  F1 Score:          {self._metrics.get('f1', 'N/A'):>10.4f}")
        lines.append(f"  FPR:               {self._metrics.get('fpr', 'N/A'):>10.4f}")
        lines.append(f"  FNR:               {self._metrics.get('fnr', 'N/A'):>10.4f}")
        lines.append(f"  MCC:               {self._metrics.get('mcc', 'N/A'):>10.4f}")
        lines.append(f"  Balanced Acc:      {self._metrics.get('balanced_accuracy', 'N/A'):>10.4f}")
        if "auc" in self._metrics:
            lines.append(f"  AUC:               {self._metrics['auc']:>10.4f}")
        lines.append(f"  Confusion Matrix:  [[{self._confusion_matrix[0][0]}, {self._confusion_matrix[0][1]}],")
        lines.append(f"                     [{self._confusion_matrix[1][0]}, {self._confusion_matrix[1][1]}]]")
        lines.append(f"  Total Samples:     {len(self.y_true):>10d}")
        return "\n".join(lines)


def compute_calibration(
    y_true: List[int], y_scores: List[float], n_bins: int = 10
) -> Dict[str, Any]:
    y_true = np.array(y_true, dtype=int)
    y_scores = np.array(y_scores, dtype=float)

    if len(y_true) == 0:
        return {"bins": [], "accuracy": [], "confidence": [], "ece": float("nan")}

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_scores, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    bin_acc = np.zeros(n_bins)
    bin_conf = np.zeros(n_bins)
    bin_counts = np.zeros(n_bins)

    for i in range(n_bins):
        mask = bin_indices == i
        cnt = int(np.sum(mask))
        bin_counts[i] = cnt
        if cnt > 0:
            bin_acc[i] = float(np.mean(y_true[mask]))
            bin_conf[i] = float(np.mean(y_scores[mask]))

    ece = float(np.sum(bin_counts * np.abs(bin_acc - bin_conf)) / np.sum(bin_counts)) if np.sum(bin_counts) > 0 else 0.0

    return {
        "bins": bins.tolist(),
        "accuracy": bin_acc.tolist(),
        "confidence": bin_conf.tolist(),
        "counts": bin_counts.tolist(),
        "ece": ece,
        "n_bins": n_bins,
    }


def compute_roc_curve(
    y_true: List[int], y_scores: List[float]
) -> Dict[str, Any]:
    y_true = np.array(y_true, dtype=int)
    y_scores = np.array(y_scores, dtype=float)

    if len(np.unique(y_true)) < 2:
        return {"fpr": [], "tpr": [], "thresholds": [], "auc": float("nan")}

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)

    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
        "auc": float(roc_auc),
    }


def compute_pr_curve(
    y_true: List[int], y_scores: List[float]
) -> Dict[str, Any]:
    y_true = np.array(y_true, dtype=int)
    y_scores = np.array(y_scores, dtype=float)

    if len(np.unique(y_true)) < 2 or np.sum(y_true == 1) == 0:
        return {"precision": [], "recall": [], "average_precision": float("nan")}

    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    avg_precision = float(np.sum((recall[:-1] - recall[1:]) * precision[:-1]) if len(precision) > 1 else 0.0)

    return {
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "average_precision": avg_precision,
    }


def find_optimal_threshold(
    y_true: List[int], y_scores: List[float], metric: str = "f1"
) -> Dict[str, Any]:
    y_true = np.array(y_true, dtype=int)
    y_scores = np.array(y_scores, dtype=float)

    if len(np.unique(y_true)) < 2:
        return {"threshold": 0.5, "metric_value": float("nan"), "metric": metric}

    thresholds = np.linspace(0.01, 0.99, 99)
    best_val = -1.0
    best_thresh = 0.5

    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)
        if metric == "f1":
            val = f1_score(y_true, y_pred, zero_division=0)
        elif metric == "precision":
            val = precision_score(y_true, y_pred, zero_division=0)
        elif metric == "recall":
            val = recall_score(y_true, y_pred, zero_division=0)
        elif metric == "balanced_accuracy":
            val = balanced_accuracy_score(y_true, y_pred)
        elif metric == "mcc":
            val = matthews_corrcoef(y_true, y_pred)
        else:
            val = f1_score(y_true, y_pred, zero_division=0)

        if val > best_val:
            best_val = float(val)
            best_thresh = float(thresh)

    return {"threshold": best_thresh, "metric_value": best_val, "metric": metric}


def regression_check(
    baseline: Dict[str, float],
    current: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    if thresholds is None:
        thresholds = {
            "accuracy": -0.01, "precision": -0.02, "recall": -0.02,
            "f1": -0.02, "auc": -0.02, "mcc": -0.05,
            "balanced_accuracy": -0.02,
        }

    all_metrics = set(baseline.keys()) | set(current.keys())
    results: Dict[str, Any] = {"regressed": False, "changes": {}, "improved": [], "degraded": []}

    for metric in all_metrics:
        if metric in ("tp", "fp", "fn", "tn", "confusion_matrix", "roc_curve", "pr_curve"):
            continue
        b_val = baseline.get(metric)
        c_val = current.get(metric)
        if b_val is None and c_val is None:
            continue
        if b_val is None:
            results["changes"][metric] = {"baseline": None, "current": c_val, "delta": None, "status": "new"}
            continue
        if c_val is None:
            results["changes"][metric] = {"baseline": b_val, "current": None, "delta": None, "status": "removed"}
            continue

        delta = float(c_val) - float(b_val)
        status = "unchanged"
        if metric in thresholds:
            thr = thresholds[metric]
            if delta < thr:
                status = "degraded"
                results["degraded"].append(metric)
                results["regressed"] = True
            elif delta > -thr:
                status = "improved"
                results["improved"].append(metric)

        results["changes"][metric] = {
            "baseline": float(b_val),
            "current": float(c_val),
            "delta": round(delta, 6),
            "status": status,
        }

    return results


def format_metrics_table(metrics: Dict[str, Any]) -> str:
    key_display = {
        "accuracy": "Accuracy", "precision": "Precision", "recall": "Recall",
        "f1": "F1", "fpr": "FPR", "fnr": "FNR", "auc": "AUC",
        "mcc": "MCC", "balanced_accuracy": "Bal.Acc",
        "tp": "TP", "fp": "FP", "fn": "FN", "tn": "TN",
    }

    rows = [("Metric", "Value")]
    rows.append(("─" * 15, "─" * 15))

    for key, disp in key_display.items():
        if key in metrics:
            val = metrics[key]
            if isinstance(val, float):
                rows.append((disp, f"{val:.4f}"))
            else:
                rows.append((disp, str(val)))

    cm = metrics.get("confusion_matrix")
    if cm and len(cm) == 2 and len(cm[0]) == 2:
        rows.append(("CM_TN", str(cm[0][0])))
        rows.append(("CM_FP", str(cm[0][1])))
        rows.append(("CM_FN", str(cm[1][0])))
        rows.append(("CM_TP", str(cm[1][1])))

    col1_w = max(len(r[0]) for r in rows) + 2
    col2_w = max(len(r[1]) for r in rows) + 2
    total_w = col1_w + col2_w + 3

    lines = ["┌" + "─" * total_w + "┐"]
    for i, (k, v) in enumerate(rows):
        sep = "├" + "─" * total_w + "┤" if i == 1 else ""
        if sep:
            lines.append(sep)
        lines.append(f"│ {k:<{col1_w-1}}│ {v:>{col2_w-1}}│")
    lines.append("└" + "─" * total_w + "┘")

    return "\n".join(lines)
