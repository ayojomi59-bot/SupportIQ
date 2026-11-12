"""Run a local, reproducible evaluation against labelled support-ticket examples."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from supportiq.analyzer import analyze_ticket

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "eval_tickets.jsonl"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load JSONL examples and validate required fields and unique IDs."""
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {"id", "subject", "message", "category", "sentiment", "urgency"}
    seen: set[str] = set()
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Example is missing fields: {sorted(missing)}")
        if row["id"] in seen:
            raise ValueError(f"Duplicate example id: {row['id']}")
        seen.add(row["id"])
    if not rows:
        raise ValueError("Evaluation dataset is empty.")
    return rows


def _field_metrics(expected: list[str], actual: list[str]) -> dict[str, Any]:
    labels = sorted(set(expected) | set(actual))
    accuracy = sum(left == right for left, right in zip(expected, actual)) / len(expected)
    per_class = {}
    f1_values = []
    for label in labels:
        tp = sum(e == label and a == label for e, a in zip(expected, actual))
        fp = sum(e != label and a == label for e, a in zip(expected, actual))
        fn = sum(e == label and a != label for e, a in zip(expected, actual))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3), "support": expected.count(label)}
        if expected.count(label):
            f1_values.append(f1)
    return {
        "accuracy": round(accuracy, 3),
        "macro_f1": round(sum(f1_values) / len(f1_values), 3) if f1_values else 0.0,
        "per_class": per_class,
    }


def evaluate(rows: list[dict[str, Any]], *, use_ai: bool = True) -> dict[str, Any]:
    """Score category, sentiment, urgency and complete-record exact match."""
    expected = {field: [] for field in ("category", "sentiment", "urgency")}
    actual = {field: [] for field in expected}
    failures = []
    exact = 0

    for row in rows:
        prediction = analyze_ticket(row["subject"], row["message"], use_ai=use_ai)
        predicted = {
            "category": prediction.category,
            "sentiment": prediction.sentiment,
            "urgency": prediction.urgency,
        }
        matched = True
        for field in expected:
            expected[field].append(row[field])
            actual[field].append(predicted[field])
            matched = matched and row[field] == predicted[field]
        exact += int(matched)
        if not matched:
            failures.append({
                "id": row["id"],
                "expected": {field: row[field] for field in expected},
                "predicted": predicted,
            })

    return {
        "mode": "ai" if use_ai else "deterministic",
        "examples": len(rows),
        "exact_match_accuracy": round(exact / len(rows), 3),
        "metrics": {field: _field_metrics(expected[field], actual[field]) for field in expected},
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--baseline", action="store_true", help="Force deterministic rules, even if an API key exists.")
    parser.add_argument("--min-exact-match", type=float, default=None, help="Optional 0-1 pass threshold.")
    args = parser.parse_args()
    if args.min_exact_match is not None and not 0 <= args.min_exact_match <= 1:
        parser.error("--min-exact-match must be between 0 and 1.")

    result = evaluate(load_dataset(args.dataset), use_ai=not args.baseline)
    print(json.dumps(result, indent=2))
    if args.min_exact_match is not None and result["exact_match_accuracy"] < args.min_exact_match:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
