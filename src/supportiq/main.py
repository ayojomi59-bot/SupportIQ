"""FastAPI application entry point."""

from fastapi import FastAPI

from supportiq import __version__
from supportiq.analyzer import analyze_ticket
from supportiq.schemas import TicketAnalysisResponse, TicketRequest

app = FastAPI(
    title="SupportIQ API",
    description="Human-in-the-loop customer support ticket intelligence.",
    version=__version__,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supportiq", "version": __version__}


@app.post(
    "/api/v1/tickets/analyze",
    response_model=TicketAnalysisResponse,
    tags=["tickets"],
)
def analyze(request: TicketRequest) -> TicketAnalysisResponse:
    result = analyze_ticket(request.subject, request.message)
    return TicketAnalysisResponse(**result.__dict__)
