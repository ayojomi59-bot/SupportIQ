"""FastAPI application entry point and ticket API."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from supportiq import __version__
from supportiq import database
from supportiq.analyzer import analyze_ticket
from supportiq.schemas import (
    TicketAnalysisResponse, TicketRecord, TicketRequest, TicketStatusUpdate,
)

app = FastAPI(
    title="SupportIQ API",
    description="Human-in-the-loop customer support ticket intelligence.",
    version=__version__,
)


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supportiq", "version": __version__}


@app.post("/api/v1/tickets/analyze", response_model=TicketAnalysisResponse, tags=["tickets"])
def analyze(request: TicketRequest) -> TicketAnalysisResponse:
    result = analyze_ticket(request.subject, request.message)
    return TicketAnalysisResponse(**result.__dict__)


@app.post("/api/v1/tickets", response_model=TicketRecord, status_code=201, tags=["tickets"])
def create_ticket(request: TicketRequest) -> dict:
    analysis = analyze_ticket(request.subject, request.message)
    return database.create_ticket(request.subject, request.message, analysis)


@app.get("/api/v1/tickets", response_model=list[TicketRecord], tags=["tickets"])
def get_tickets(status: str | None = Query(default=None)) -> list[dict]:
    if status and status not in {"all", "open", "in_progress", "resolved"}:
        raise HTTPException(status_code=422, detail="Unsupported ticket status")
    return database.list_tickets(status)


@app.patch("/api/v1/tickets/{ticket_id}", response_model=TicketRecord, tags=["tickets"])
def change_ticket_status(ticket_id: int, update: TicketStatusUpdate) -> dict:
    ticket = database.update_status(ticket_id, update.status)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/api/v1/dashboard/stats", tags=["dashboard"])
def get_dashboard_stats() -> dict[str, int]:
    return database.dashboard_stats()
