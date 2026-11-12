"""API request and response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=10_000)


class TicketAnalysisResponse(BaseModel):
    category: str
    sentiment: str
    urgency: str
    confidence: float
    rationale: list[str]
    suggested_reply: str
    requires_human_review: bool = True


class TicketRecord(TicketAnalysisResponse):
    id: int
    subject: str
    message: str
    status: Literal["open", "in_progress", "resolved"]
    created_at: str


class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]
