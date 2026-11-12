import json

import pytest

from scripts.evaluate import _field_metrics, load_dataset


def test_field_metrics_reports_accuracy_and_macro_f1():
    result = _field_metrics(
        ["billing", "shipping", "billing"],
        ["billing", "billing", "billing"],
    )
    assert result["accuracy"] == pytest.approx(2 / 3, abs=0.001)
    assert result["per_class"]["shipping"]["recall"] == 0.0


def test_dataset_rejects_duplicate_ids(tmp_path):
    row = {
        "id": "same",
        "subject": "a",
        "message": "b",
        "category": "general",
        "sentiment": "neutral",
        "urgency": "normal",
    }
    path = tmp_path / "duplicate.jsonl"
    path.write_text(
        json.dumps(row) + "\n" + json.dumps(row),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate"):
        load_dataset(path)


def test_evaluation_uses_deterministic_mode(monkeypatch):
    from scripts import evaluate as evaluator

    class Result:
        category = "billing"
        sentiment = "negative"
        urgency = "high"

    calls = []
    monkeypatch.setattr(
        evaluator,
        "analyze_ticket",
        lambda subject, message, use_ai: (calls.append(use_ai) or Result()),
    )
    rows = [
        {
            "id": "one",
            "subject": "refund",
            "message": "angry",
            "category": "billing",
            "sentiment": "negative",
            "urgency": "high",
        }
    ]
    result = evaluator.evaluate(rows, use_ai=False)
    assert calls == [False]
    assert result["exact_match_accuracy"] == 1.0
