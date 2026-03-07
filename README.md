# stockVis

A learning-oriented full-stack project to analyze portfolio look-through exposure.

## What This App Does

You input holdings as ticker + share count for both ETFs and single stocks.

Example input:
- VOO, 3 shares
- MSFT, 10 shares

The app then:
1. Expands ETF holdings into underlying constituents.
2. Merges overlap with direct single-stock holdings.
3. Calculates each stock's percentage exposure in the full portfolio.
4. Shows only rows above a user threshold.

## Core Rules

- Threshold range: 1% to 100%.
- UI layout:
  - Left panel: all inputs and controls.
  - Right panel: analysis result.

## Planned Tech Stack

- Frontend: Vue 3 + Vite + Pinia
- Backend: FastAPI + Pydantic + SQLAlchemy (+ Alembic for migrations)
- Database: SQLite
- Deployment: Docker / Docker Compose

Notes:
- Start with fetch + Pinia for frontend data flow.
- Scheduler is optional for v1; on-demand ETF refresh is enough.

## Status

- Current repository state: README only.
- Frontend/backend scaffolding will be created manually next.

## Suggested Build Phases

### Phase 0: Scaffold Frameworks
- Create Vue app in `frontend/` with Vite.
- Create FastAPI app in `backend/` with a `/health` endpoint.

### Phase 1: UI Skeleton
- Two-panel layout.
- Left panel: holdings rows + threshold control.
- Right panel: placeholder result table.

### Phase 2: API Contract
- Define request/response schema for analysis endpoint.
- Connect frontend form -> backend analyze endpoint.

### Phase 3: Portfolio Math
- Implement overlap-aware aggregation logic.
- Add threshold filtering and sorting.

### Phase 4: Persistence
- Add SQLite models.
- Save user holdings and cached ETF constituents.

### Phase 5: Data Provider Integration
- Add ETF constituent data provider adapter.
- Handle stale/missing provider data gracefully.

### Phase 6: Containerization
- Add Dockerfiles and `docker-compose.yml`.
- Run frontend + backend together locally.

## Manual Scaffold Commands

### Frontend (Vue + Vite)

```bash
cd /Users/ray/4Fun/stockVis
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm run dev
```

### Backend (FastAPI)

```bash
cd /Users/ray/4Fun/stockVis
mkdir backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
cat > main.py <<'PY'
from fastapi import FastAPI

app = FastAPI(title="stockVis API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
PY
uvicorn main:app --reload
```

## API Direction (Draft)

- `GET /health` -> service status.
- `POST /analyze` -> input holdings + threshold, output exposure breakdown.

Request draft:

```json
{
  "holdings": [
    { "ticker": "VOO", "shares": 3 },
    { "ticker": "MSFT", "shares": 10 }
  ],
  "threshold_percent": 5
}
```

Response draft:

```json
{
  "threshold_percent": 5,
  "rows": [
    {
      "ticker": "MSFT",
      "total_percent": 12.4,
      "from_etf_percent": 8.1,
      "direct_percent": 4.3
    }
  ]
}
```

## Development Principles

- Build one file at a time.
- Keep each commit focused and small.
- Prefer clarity over cleverness.
- Validate behavior with sample portfolios before adding complexity.
