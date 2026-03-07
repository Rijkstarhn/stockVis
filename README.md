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
  - Right panel: exposure chart + analysis table.

## UI Wireframe (ASCII)

```text
+--------------------------------------------------------------------------------------+
|                                      stockVis                                        |
+-------------------------------------------+------------------------------------------+
| LEFT PANEL (Inputs / Controls)            | RIGHT PANEL (Analysis + Chart)          |
|                                           |                                          |
| Holdings                                  | Exposure Breakdown Chart                 |
| +--------+---------+--------+             | +--------------------------------------+ |
| | Ticker | Shares  | Action |             | |  (Bar/Pie chart of Total %)         | |
| +--------+---------+--------+             | |  MSFT  ████████████ 12.4%           | |
| | VOO    | 3       | [x]    |             | |  AAPL  █████████    9.8%            | |
| | MSFT   | 10      | [x]    |             | |  ...                                 | |
| | [....] | [....]  | [x]    |             | +--------------------------------------+ |
| +--------+---------+--------+             |                                          |
|                                           | Exposure Table (> threshold)            |
| [+ Add Row]                               | +--------+----------+---------+---------+
|                                           | | Ticker | Total %  | ETF %   | Direct %|
| Threshold (%)                             | +--------+----------+---------+---------+
| [----|------ slider ------|----]  5%      | | MSFT   | 12.4     | 8.1     | 4.3     |
|                                           | | AAPL   |  9.8     | 9.8     | 0.0     |
| [ Analyze ]                               | | ...    | ...      | ...     | ...     |
|                                           | +--------+----------+---------+---------+
+-------------------------------------------+------------------------------------------+
```

## Planned Tech Stack

- Frontend: Vue 3 + Vite + Pinia
- Backend: FastAPI + Pydantic + SQLAlchemy (+ Alembic for migrations)
- Database: SQLite
- Deployment: Docker / Docker Compose
