from fastapi.testclient import TestClient

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
