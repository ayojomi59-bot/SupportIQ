# SupportIQ

AI-powered customer support intelligence for classifying tickets, detecting sentiment and urgency, and drafting helpful replies.

## What it does

- Classifies incoming support tickets into practical categories.
- Uses OpenAI structured outputs for richer analysis when an API key is configured.
- Falls back to explainable local rules if no key is configured or the AI provider is unavailable.
- Suggests a response for a human support agent to review.
- Provides ticket history, status tracking, dashboard statistics, and a FastAPI REST API.

> **Human-in-the-loop:** SupportIQ suggests classifications and replies. It does not send messages, close tickets, or take customer-facing actions automatically. Model output is validated before it is used.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn supportiq.main:app --reload
```

Open http://127.0.0.1:8000 for the dashboard and http://127.0.0.1:8000/docs for the API docs.

## Optional OpenAI integration

SupportIQ works without an API key. To enable model-assisted analysis, copy `.env.example` to `.env`, add your key, and load the variables in your shell or development environment:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

The application uses the OpenAI Responses API with a Pydantic schema, disables response storage for these requests, and falls back to the deterministic analyzer if the provider fails. Never commit your real `.env` file or expose your API key in screenshots or logs.

## API

- `GET /health` — service health
- `POST /api/v1/tickets/analyze` — classify a ticket and draft a suggested reply
- `POST /api/v1/tickets` — analyze and save a ticket
- `GET /api/v1/tickets` — list tickets, optionally filtered by status
- `PATCH /api/v1/tickets/{ticket_id}` — update ticket status
- `GET /api/v1/dashboard/stats` — dashboard counts

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tickets/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"subject":"Refund not received","message":"I have waited two weeks for my refund and I am frustrated."}'
```

## Project structure

```
src/supportiq/       Application, analysis logic, database, and dashboard
tests/               Automated tests (no live API key required)
.github/workflows/   Continuous integration
```

## Roadmap

- [x] API foundation and deterministic ticket analysis
- [x] Human-reviewed response suggestions
- [x] Persistent ticket history and agent dashboard
- [x] Optional LLM-powered analysis with structured output and deterministic fallback
- [ ] Knowledge-base retrieval and cited answer suggestions
- [ ] Evaluation dataset and quality metrics

## Development

```bash
ruff check .
pytest
```

## License

MIT
