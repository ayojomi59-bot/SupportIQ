from fastapi.testclient import TestClient

from supportiq import database
from supportiq.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_billing_ticket_is_classified_and_review_flagged():
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


def test_unknown_ticket_falls_back_to_general():
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
