"""Explainable baseline ticket analysis using transparent keyword signals."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketAnalysis:
    category: str
    sentiment: str
    urgency: str
    confidence: float
    rationale: list[str]
    suggested_reply: str


CATEGORY_KEYWORDS = {
    "billing": ("refund", "invoice", "payment", "charged", "billing", "subscription"),
    "technical": ("error", "bug", "broken", "crash", "not working", "issue", "failed"),
    "account": ("login", "password", "account", "sign in", "access", "locked"),
    "shipping": ("delivery", "shipping", "shipment", "tracking", "package", "order"),
}
NEGATIVE_WORDS = {
    "angry", "bad", "broken", "disappointed", "frustrated", "hate", "issue",
    "late", "never", "problem", "terrible", "unacceptable", "waiting", "waited",
    "wrong", "not", "received",
}
POSITIVE_WORDS = {
    "amazing", "excellent", "happy", "helpful", "love", "perfect", "please",
    "thanks", "thank", "wonderful", "great",
}
URGENT_WORDS = (
    "asap", "immediately", "urgent", "emergency", "critical",
    "cannot work", "locked out", "data loss",
)


def analyze_ticket(subject: str, message: str) -> TicketAnalysis:
    """Analyze a ticket using transparent keyword rules."""
    text = f"{subject} {message}".lower()
    words = set(re.findall(r"[a-z']+", text))
    category_scores = {
        category: sum(1 for keyword in keywords if keyword in text)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] == 0:
        category, confidence = "general", 0.45
    else:
        total = sum(category_scores.values())
        confidence = min(0.95, 0.65 + category_scores[best_category] / max(total, 1) * 0.3)
        category = best_category

    negative = len(words & NEGATIVE_WORDS)
    positive = len(words & POSITIVE_WORDS)
    sentiment = "negative" if negative > positive else "positive" if positive > negative else "neutral"
    urgent = any(term in text for term in URGENT_WORDS)
    urgency = "high" if urgent or (sentiment == "negative" and negative >= 2) else "normal"

    rationale = [f"Category selected from keyword matches: {category}."]
    rationale.append(f"Sentiment signals: {negative} negative and {positive} positive terms.")
    rationale.append("Urgency keywords detected." if urgent else "No explicit urgency keyword detected.")
    replies = {
        "billing": "Thanks for contacting us about your billing concern. We’ll review the payment details and help clarify the next steps.",
        "technical": "Thanks for reporting this issue. Please share any error message and the steps that led to it so our team can investigate.",
        "account": "Thanks for reaching out. We can help with your account access. Please do not share your password or other secret credentials.",
        "shipping": "Thanks for checking on your order. We’ll review the shipment details and help you understand its current status.",
        "general": "Thanks for contacting us. We’ve received your message and our support team will review it and follow up.",
    }
    return TicketAnalysis(category, sentiment, urgency, round(confidence, 2), rationale, replies[category])
