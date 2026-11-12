from fastapi.testclient import TestClient

from supportiq import analyzer, database
from supportiq.analyzer import AIAnalysis
from supportiq.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_billing_ticket_is_classified_and_review_flagged(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/tickets/analyze",
        json={
            "subject": "Refund not received",
            "message": "I have waited two weeks for my refund and I am frustrated.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "billing"
    assert data["sentiment"] == "negative"
    assert data["urgency"] == "high"
    assert data["requires_human_review"] is True
    assert data["suggested_reply"]


def test_unknown_ticket_falls_back_to_general(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/tickets/analyze",
        json={"subject": "Hello", "message": "I have a question."},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "general"


def test_empty_message_is_rejected():
    response = client.post(
        "/api/v1/tickets/analyze",
        json={"subject": "Help", "message": ""},
    )
    assert response.status_code == 422


def test_ticket_is_saved_listed_and_status_updated(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    created = client.post(
        "/api/v1/tickets",
        json={"subject": "Login issue", "message": "I cannot sign in to my account."},
    )
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["id"] == 1
    assert client.get("/api/v1/tickets").json()[0]["subject"] == "Login issue"
    assert client.get("/api/v1/dashboard/stats").json()["open"] == 1

    updated = client.patch("/api/v1/tickets/1", json={"status": "in_progress"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"
    assert client.get("/api/v1/dashboard/stats").json()["in_progress"] == 1


def test_missing_ticket_update_returns_404():
    response = client.patch("/api/v1/tickets/999", json={"status": "resolved"})
    assert response.status_code == 404


def test_openai_analysis_is_used_when_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    expected = AIAnalysis(
        category="billing",
        sentiment="negative",
        urgency="high",
        confidence=0.93,
        rationale=["Customer reports an unresolved refund."],
        suggested_reply="We’re sorry about the delay. Our team will review this with you.",
    )
    calls = {}

    def fake_provider(subject, message, api_key, model):
        calls.update(subject=subject, message=message, api_key=api_key, model=model)
        return expected

    monkeypatch.setattr(analyzer, "_analyze_with_openai", fake_provider)
    result = analyzer.analyze_ticket("Refund delay", "Where is my refund?")
    assert result.category == "billing"
    assert result.confidence == 0.93
    assert calls["api_key"] == "test-key"
    assert calls["model"] == "test-model"


def test_openai_failure_uses_deterministic_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def failing_provider(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(analyzer, "_analyze_with_openai", failing_provider)
    result = analyzer.analyze_ticket("Refund not received", "I am frustrated and still waiting.")
    assert result.category == "billing"
    assert result.urgency == "high"
