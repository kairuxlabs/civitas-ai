<div align="center">


# Civitas AI

**AI-powered Urban Operating System for Hanoi**

An intelligent city management platform that ingests real-time weather and air quality data, processes it through a 7-agent sequential pipeline powered by Google Gemini, and delivers actionable insights to city operators through a Mission Control dashboard with live WebSocket streaming.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/kairus-dev/civitas-ai/ci.yml?branch=main&label=CI&style=flat-square)](../../actions/workflows/ci.yml)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [API Reference](#api-reference) · [Testing](#testing) · [Deployment](#deployment)

</div>

---

## Features

- **Real-time monitoring** — Weather and AQI data fetched every 15 minutes from Open-Meteo and OpenAQ across all 12 Hanoi districts
- **7-agent AI pipeline** — Sequential graph (traffic → environment → event → citizen → knowledge → decision → explanation) powered by Google Gemini
- **Live WebSocket streaming** — Agent pipeline progress broadcast in real time; operators watch each step complete
- **Mission Control dashboard** — SVG district map, KPI bar, AI Copilot chat, real-time Decision Report with Approve/Reject
- **What-If Simulator** — Scenario testing (heavy rain, air pollution, major event, heatwave) with AI predictions
- **Human-in-the-loop** — Decisions with confidence < 75% or flood risk flagged as `high` require operator approval
- **Decision Timeline** — Persistent log of all agent decisions with confidence scores and full explanations

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript 5.5, Vite, Tailwind CSS, TanStack Query, Axios |
| **Backend** | FastAPI 0.111, Python 3.11+, SQLAlchemy 2.0 (async), Pydantic v2 |
| **AI / Agents** | Google Gemini via LangChain (sequential agent graph, no LangGraph dependency) |
| **Database** | PostgreSQL 15 (production via Neon.tech), SQLite (local dev) |
| **Scheduler** | APScheduler — triggers full data pipeline every 15 minutes |
| **Data Sources** | [Open-Meteo](https://open-meteo.com) (weather), [OpenAQ](https://openaq.org) (air quality) |
| **Testing** | pytest + httpx (backend), Vitest + Testing Library (frontend), Playwright (E2E) |
| **CI/CD** | GitHub Actions → Render (backend) + Vercel (frontend) + Neon.tech (database) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  React Frontend (:3000)                          │
│        Mission Control: Map · Copilot · Simulator · Timeline     │
└────────────────────┬────────────────────────┬───────────────────┘
                     │  /api/* (Vite proxy)   │  /ws (WebSocket)
┌────────────────────▼────────────────────────▼───────────────────┐
│                    FastAPI Backend (:8000)                        │
│  GET /api/districts   GET /api/scores   GET /api/timeline        │
│  POST /api/chat       POST /api/simulate                         │
│  POST /api/decisions/{id}/approve|reject                         │
└───────┬─────────────────────────────┬────────────────────────────┘
        │                             │
┌───────▼──────────┐    ┌─────────────▼───────────────────────────┐
│   PostgreSQL      │    │           Agent Pipeline                 │
│                  │    │                                          │
│  districts       │    │  traffic → environment → event           │
│  weather         │◄───┤  → citizen → knowledge → decision        │
│  aqi             │    │  → explanation                           │
│  city_score      │    │                                          │
│  agent_decisions │    │  Each step broadcasts WebSocket events   │
└───────────────────┘   │  Decisions saved to DB + returned        │
        ▲               └──────────────────────────────────────────┘
        │
┌───────┴──────────────┐
│  APScheduler (15min)  │
│  WeatherPipeline      │  ← Open-Meteo API
│  AQIPipeline          │  ← OpenAQ API
│  FeedbackPipeline     │  ← synthetic citizen reports
│  CityScoreService     │  ← derives scores from sensor data
└───────────────────────┘
```

### Agent Pipeline

Every `/api/chat` and `/api/simulate` call runs a sequential 7-step pipeline:

```
Traffic → Environment → Event → Citizen → Knowledge → Decision → Explanation
```

Each agent is a sync function called via `asyncio.to_thread()`. Between steps, WebSocket events are broadcast so the UI shows live progress. The Knowledge Agent retrieves relevant SOPs from a static keyword index. The Decision Agent synthesises all analyses into a structured response. If `confidence < 75` or `flood_risk == "high"`, the decision is flagged as `requires_approval = True`.

### Score Derivation

`CityScoreService` derives scores from the latest sensor readings per district:

| Score | Formula |
|---|---|
| `traffic_score` | `100 − (aqi_index / 3)` |
| `environment_score` | `100 − (pm25 / 1.5)` |
| `risk_score` | `(rain × 5) + (aqi_index / 4)` |
| `overall_score` | mean of traffic, environment, citizen, `(100 − risk)` |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)

### Docker (recommended)

```bash
git clone https://github.com/kairus-dev/civitas-ai.git
cd civitas-ai

echo "GEMINI_API_KEY=your_key_here" > .env
docker-compose up
```

All services start automatically. PostgreSQL is initialised with the schema and 12 Hanoi districts on first boot.

| Service | URL | Description |
|---|---|---|
| **Frontend** | http://localhost:3000 | React Mission Control |
| **Backend API** | http://localhost:8000 | FastAPI |
| **Swagger UI** | http://localhost:8000/docs | Interactive API docs |
| **Adminer** | http://localhost:8080 | Database browser |

### Local dev (without Docker)

**Backend:**
```bash
cd backend
cp .env.example .env
# Set DATABASE_URL=sqlite+aiosqlite:///./civitas_dev.db  (tables auto-created)
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Scheduler (separate terminal — runs pipelines every 15 min)
python -m src.scheduler.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev     # http://localhost:3000 — proxies /api/* to :8000
```

---

## API Reference

### Districts & Scores

```http
GET /api/districts
```
Returns all 12 Hanoi districts.

```http
GET /api/scores
GET /api/scores/{district_id}
```
Returns latest computed city scores per district.

```http
GET /api/aqi/history/{district_id}?limit=24
```
Returns last N AQI readings for charting.

### AI Agent

```http
POST /api/chat
Content-Type: application/json

{ "query": "Tình hình ngập lụt tại quận này?", "district_id": 3 }
```

```http
POST /api/simulate
Content-Type: application/json

{ "scenario": "heavy_rain", "district_id": 3 }
```

Available scenarios: `heavy_rain` · `air_pollution` · `major_event` · `heatwave`

Both endpoints run the full 7-agent pipeline and return:

```json
{
  "prediction": {
    "next_6h_aqi_trend": "increasing",
    "flood_risk": "high",
    "traffic_disruption": "likely"
  },
  "impact": {
    "population_affected": "150,000 residents",
    "economic_impact": "high",
    "health_risk": "moderate"
  },
  "recommendations": [
    "Activate flood drainage systems",
    "Deploy traffic management at flood-prone intersections"
  ],
  "confidence": 85.0,
  "explanation": [
    "Traffic Analysis: HIGH traffic congestion risk due to heavy rain.",
    "Knowledge: Flood Emergency SOP triggered — activate drainage pumps...",
    "Confidence: 85% based on 4 data streams"
  ]
}
```

### Human-in-the-loop

```http
POST /api/decisions/{id}/approve
POST /api/decisions/{id}/reject
```

Approving or rejecting a decision broadcasts a `approval_result` WebSocket event to all connected clients.

### Timeline

```http
GET /api/timeline?limit=20
```
Returns recent agent decisions ordered by most recent.

### WebSocket

Connect at `ws://localhost:8000/ws`. Events:

| `type` | When |
|---|---|
| `pipeline_start` | Before first agent |
| `agent_update` | Before/after each agent (`status: running\|done`) |
| `pipeline_done` | After decision saved |
| `approval_needed` | When `requires_approval = true` |
| `approval_result` | After approve/reject |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | `postgresql+asyncpg://...` for prod, `sqlite+aiosqlite:///./dev.db` for local |
| `GEMINI_API_KEY` | ✅ | `""` | Get a free key at [aistudio.google.com](https://aistudio.google.com) |
| `CHROMADB_HOST` | ❌ | `localhost` | ChromaDB host (future vector search) |
| `CHROMADB_PORT` | ❌ | `8001` | ChromaDB port |

---

## Testing

Three automated test layers totalling 113 tests.

### Backend (pytest)

```bash
cd backend
pytest                          # all 26 tests
pytest -v tests/test_health.py  # single file
```

Uses SQLite in-memory — no external services required. See [docs/TESTING.md](docs/TESTING.md) for full details.

### Frontend unit (Vitest)

```bash
cd frontend
npm test            # 51 tests, single pass
npm run test:watch  # watch mode
```

### E2E (Playwright)

```bash
cd frontend
npm run e2e          # 36 tests, Chromium headless
npm run e2e:headed   # watch the browser
npm run e2e:ui       # interactive UI explorer
```

Suites 01–04 mock all API calls and run without a backend. Suite 05 is a full-stack integration test that auto-skips if the backend is unreachable.

---

## Project Structure

```
civitas-ai/
├── .github/workflows/
│   ├── ci.yml              # tests on every push/PR (4 parallel jobs)
│   └── deploy.yml          # deploy to Render + Vercel on main push
│
├── backend/
│   ├── src/
│   │   ├── agents/         # 7 agent node functions (sync, called via asyncio.to_thread)
│   │   ├── api/routes/     # FastAPI routers: districts, scores, chat, simulate, decisions, timeline, ws
│   │   ├── orchestrator/
│   │   │   └── graph.py    # sequential pipeline runner + WebSocket broadcasting
│   │   ├── pipelines/      # WeatherPipeline, AQIPipeline, FeedbackPipeline
│   │   ├── repositories/   # async SQLAlchemy query helpers
│   │   ├── services/       # CityScoreService
│   │   ├── scheduler/      # APScheduler entry point
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   ├── ws/             # WebSocket connection manager
│   │   └── utils/          # pydantic-settings config, logger
│   ├── scripts/
│   │   └── migrate_neon.py # one-time Neon.tech migration + district seed
│   ├── tests/              # 26 async pytest tests
│   ├── Dockerfile.prod     # production Docker image (2 Uvicorn workers)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/CommandCenterPage.tsx  # main Mission Control layout
│   │   ├── components/
│   │   │   ├── HanoiMap.tsx            # SVG district map with click handlers
│   │   │   ├── SimulatorModal.tsx      # scenario selector modal
│   │   │   └── AgentGraph.tsx          # live pipeline progress SVG
│   │   ├── hooks/useWebSocket.ts       # auto-reconnecting WebSocket hook
│   │   ├── services/api.ts             # Axios client
│   │   └── types/index.ts             # shared TypeScript interfaces
│   ├── e2e/                            # Playwright test suites (01-05)
│   ├── playwright.config.ts
│   └── vercel.json                     # SPA rewrite + build config
│
├── render.yaml             # Render Blueprint for backend service
├── docker-compose.yml      # local full-stack dev
└── docs/
    ├── DEPLOYMENT.md       # step-by-step Neon + Render + Vercel setup
    └── TESTING.md          # test layer details + Playwright guide
```

---

## Database Schema

| Table | Description |
|---|---|
| `districts` | 12 Hanoi districts with optional geometry |
| `weather` | Per-district readings: temperature, humidity, rain, wind speed |
| `aqi` | Per-district readings: PM2.5, PM10, CO, NO₂, AQI index |
| `events` | City events with impact level |
| `citizen_feedback` | Citizen reports with sentiment |
| `city_score` | Derived scores: traffic, environment, citizen, risk, overall |
| `agent_decisions` | Full pipeline output: prediction, impact, recommendations, confidence, explanation, approval status |

All tables carry a `city_id` column (default `'hanoi'`) for future multi-city support.

---

## Deployment

Production stack: **Neon.tech** (PostgreSQL) + **Render** (backend) + **Vercel** (frontend), orchestrated by GitHub Actions.

Quick setup overview:

1. **Neon.tech** — Create project → copy connection string → run `python -m scripts.migrate_neon`
2. **Render** — New Web Service → Docker → set `DATABASE_URL` + `GEMINI_API_KEY` → copy deploy hook URL
3. **Vercel** — `vercel link` in `frontend/` → set `VITE_API_BASE_URL` + `VITE_WS_URL` → get token/IDs
4. **GitHub Secrets** — Add `RENDER_DEPLOY_HOOK_URL`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the complete step-by-step guide.

---

## Knowledge Pipeline Roadmap

**v1 (current)** — manual bootstrap via `python -m src.knowledge_pipeline.bootstrap`:
- ✅ OpenStreetMap (hospitals, schools, police, fire stations, roads, bus stops, parks, rivers, buildings)
- ✅ Wikipedia (8 topics: Hanoi, Flood, Natural disaster, Transportation, Public health, Air pollution, Climate change, Emergency management)
- ✅ GeoJSON district boundaries (derived from OSM admin boundaries)
- ✅ Wikidata (best-effort enrichment of OSM entities)
- ✅ Government PDF (fully functional, ships with an empty `config/pdf_sources.yaml` — add entries to activate)
- ✅ Neo4j city entity graph + Qdrant `city_knowledge` collection

**v2 (planned)**:
- `scheduler.py`: weekly automated Wikipedia refresh (stubbed in v1 — see `src/knowledge_pipeline/scheduler.py`)
- Incremental updates, RSS/news source integration, automated PDF discovery

**v3 (future)**:
- Streaming ingestion (Kafka or equivalent), real-time knowledge updates

---

## AI Gateway (`backend/src/ai/`)

Centralizes all OpenRouter/Nemotron calls behind one gateway so no agent talks to the network directly:

- `gateway.py` — `call_openrouter(models, payload, endpoint)`: tries each model in a fallback list, returns the first successful response or `None`.
- `safety.py` — `check_safety(text)`: content-safety check, fails **open** (`safe=True`) if the gateway is unreachable.
- `embedding.py` — `embed(text)`: standalone embedding call (not wired into the existing Gemini-backed `city_knowledge`/`cityos_sop` Qdrant collections).
- `reranker.py` — `rerank(query, documents, top_k)`: reorders candidates, falls back to original order on failure.
- `planner.py` — `complete(prompt, context)`: safety-checked completion (pre- and post-check).

Wired into `KnowledgeMemory._qdrant_search` (`src/runtime/memory.py`) as an optional post-processing step: widens the Qdrant candidate set and reranks it before truncating to `k`.

**Gemini quota fallback:** `call_gemini()` (`src/agents/gemini_client.py`) — used by all 7 agents and the knowledge pipeline's entity extractor — now falls back to `planner.complete()` (OpenRouter/Nemotron) whenever the Gemini call fails, e.g. on free-tier `429 RESOURCE_EXHAUSTED`. This runs automatically once `OPENROUTER_API_KEY` is set; unaffected (same as before) when unset.

**Model slugs — live-verified 2026-07-05:** the planner model was live-tested against the real OpenRouter API and found wrong (`nvidia/nemotron-3-ultra:free` → HTTP 400); fixed to `nvidia/nemotron-3-ultra-550b-a55b:free` (confirmed HTTP 200) in `src/ai/planner.py`. `openrouter/free` (fallback) confirmed to be a real OpenRouter free-model router. The `safety`/`embedding`/`reranker` model slugs were cross-checked against OpenRouter's public NVIDIA model catalog (all matched) but not live-tested end-to-end — do one live call per function before depending on them for a demo.

**Before demoing with a real `OPENROUTER_API_KEY`:** every module in this package is tested offline (mocked gateway) — no test proves the OpenRouter model slugs or `embeddings`/`rerank` endpoint paths actually resolve. A wrong slug degrades silently to `None`/passthrough with only a log warning. Manually call `complete()`, `embed()`, `rerank()`, and `check_safety()` once each against the real API before relying on this layer.

**Inactive by default.** Every function in this package degrades gracefully (`None`/passthrough, never raises) when `OPENROUTER_API_KEY` is unset in `.env` — existing Gemini-based agents and pipelines are unaffected. Set `OPENROUTER_API_KEY` to activate.

---

## License

[MIT](LICENSE) — built by [@kairuslabs](https://github.com/kairuxlabs)
