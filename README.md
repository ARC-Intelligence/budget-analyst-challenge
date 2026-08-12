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

### Native

Backend:

```bash
cd backend && uv sync && uv run python manage.py migrate && uv run python manage.py seed && uv run --with uvicorn uvicorn config.asgi:application --reload
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

## Environment variables

| Variable | Where | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | backend | Required for chat. The OpenAI SDK reads it from the environment. |
| `OPENAI_MODEL` | backend | Optional. Defaults to `gpt-5-mini`. |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Optional. Defaults to `http://localhost:8000`. |

Django also honors `DEBUG`, `DJANGO_SECRET_KEY`, and `CORS_ALLOWED_ORIGINS`.

## The challenge

Task instructions are provided separately.

## Tests

`cd backend && uv run pytest` runs the API tests.
