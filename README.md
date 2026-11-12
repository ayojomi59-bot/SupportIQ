# SupportIQ

AI-powered customer support intelligence for classifying tickets, detecting sentiment and urgency, and drafting helpful replies.

## What it does

- Classifies incoming support tickets into practical categories.
- Detects sentiment and urgency with an explainable baseline analyzer.
- Suggests a response for a human support agent to review.
- Exposes a documented REST API with FastAPI.
- Keeps the first release deterministic and usable without API keys.

> **Human-in-the-loop:** SupportIQ suggests classifications and replies. It does not send messages, close tickets, or take customer-facing actions automatically.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn supportiq.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs.

## API

- `GET /health` — service health
- `POST /api/v1/tickets/analyze` — classify a ticket, estimate sentiment and urgency, and draft a suggested reply

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tickets/analyze \
  -H "Content-Type: application/json" \
  -d '{"subject":"Refund not received","message":"I have waited two weeks for my refund and I am very frustrated."}'
```

## Project structure

```
src/supportiq/       Application and analysis logic
tests/               Automated tests
.github/workflows/   Continuous integration
```

## Roadmap

- [x] API foundation and deterministic ticket analysis
- [x] Human-reviewed response suggestions
- [ ] Persistent ticket history and agent dashboard
- [ ] Optional LLM-powered analysis with structured output
- [ ] Knowledge-base retrieval and cited answer suggestions
- [ ] Evaluation dataset and quality metrics

## Development

```bash
ruff check .
pytest
```

## License

MIT
