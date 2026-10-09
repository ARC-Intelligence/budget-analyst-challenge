# AI Budget Analyst

A budget review workspace for comparing planned spend against actuals. Scenarios hold departmental line items with budget vs actual figures by month. A chat assistant panel is wired to a real LLM and streams replies as they are generated.

## Getting started

Copy `.env.example` to `.env` and add the API key you were sent.

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/), or [uv](https://docs.astral.sh/uv/) + Node 22 and [pnpm](https://pnpm.io/).

### Docker

```bash
docker compose up
```

The first start migrates and seeds the database automatically. Backend listens on [http://localhost:8000](http://localhost:8000), frontend on [http://localhost:3000](http://localhost:3000).

Note: the containers use their own dependency volumes, so to add a package run it inside the container, e.g. `docker compose exec frontend pnpm add <pkg>` or `docker compose exec backend uv add <pkg>`.

### Native

Backend:

```bash
cd backend && uv sync && uv run python manage.py migrate && uv run python manage.py seed && uv run uvicorn config.asgi:application --reload
```

Frontend:

```bash
cd frontend && pnpm install && pnpm dev
```

Open [http://localhost:3000](http://localhost:3000), open the scenario, and confirm the chat replies before your session.

## Where things live

| What | Where |
| --- | --- |
| Budget data models & CRUD API | `backend/budgets/` |
| Chat endpoint & agent loop | `backend/assistant/` |
| SSE client | `frontend/src/lib/chatStream.ts` |
| Chat UI | `frontend/src/components/Chat.tsx` |
| Scenario table | `frontend/src/components/ScenarioTable.tsx` |
| Your decisions | `DECISIONS.md` |

## The data

One scenario, FY2026 Operating Budget: eight departments, a dozen-ish spend categories each, one line item per department × category × month for Jan–Dec 2026, with `budget_amount` and `actual_amount`.

Actuals are booked as months close. Not every department has closed the same month, so `actual_amount` is `null` for months a department hasn't booked yet. Some line items carry a short `notes` string.

Line items also have a free-form JSON `metadata` field. Different teams fill it in differently, so keys, nesting, and coverage vary by department and many rows have none. Treat it as what it is: whatever the team happened to record.

`uv run python manage.py seed --reset` reloads the scenario from the bundled snapshot.

## Environment variables

| Variable | Where | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | backend | Required for chat. The OpenAI SDK reads it from the environment. |
| `OPENAI_MODEL` | backend | Optional. Defaults to `gpt-6-luna`. |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Optional. Defaults to `http://localhost:8000`. |

Django also honors `DEBUG`, `DJANGO_SECRET_KEY`, and `CORS_ALLOWED_ORIGINS`.

## The challenge

Task instructions are provided separately. Record your decisions in `DECISIONS.md` as you go; short is fine.

## Tests

`cd backend && uv run pytest` runs the API tests.
