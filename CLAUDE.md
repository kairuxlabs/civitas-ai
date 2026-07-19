# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CityOS (Civitas AI)** is an AI-powered urban operating system for Hanoi. Two agent pipelines coexist: a v1 sequential pipeline (Google Gemini, plain Python — despite historical naming, it does **not** use LangGraph) and a v2 event-driven multi-agent runtime (Planner → Workers → Reflection → Decision) backed by a Neo4j + Qdrant knowledge graph and an AI Gateway that routes to NVIDIA Nemotron via OpenRouter with automatic Gemini fallback. It ingests real-time weather/AQI data, generates district-level decisions and recommendations, and exposes a React dashboard for city operators.

## Commands

### Backend

```bash
# From backend/ directory — set up .env first (copy .env.example)
cd backend
pip install -r requirements.txt

# Run API server (requires PostgreSQL; Neo4j/Qdrant/OpenRouter are optional —
# every integration that needs them degrades gracefully when unset)
uvicorn src.main:app --reload --port 8000

# Run scheduler (separate process, runs the 15-min pipelines + weekly knowledge
# refresh — NOTE: src/main.py's lifespan() also starts an in-process copy of
# this scheduler, so running both this and uvicorn together double-runs the
# 15-min pipelines; this matches current docker-compose.yml behavior)
python -m src.scheduler.main

# Run all tests (uses SQLite in-memory, no external deps needed)
pytest

# Run a specific test file
pytest tests/test_health.py

# Run a specific test
pytest tests/test_health.py::test_health_endpoint
```

### Frontend

```bash
# From frontend/ directory
npm install
npm run dev          # dev server on port 3000
npm run build        # TypeScript check + Vite build
```

### Full Stack (Docker)

```bash
# Requires GEMINI_API_KEY in environment or .env at repo root
docker-compose up

# Services: backend:8000, frontend:3000, nginx:80, chromadb:8001 (unused legacy
# dependency — see Environment Variables), adminer:8080, postgres:5432.
# scheduler runs as a background service with no exposed port.
```

## Architecture

### Two Coexisting Agent Pipelines

- **v1 — sequential pipeline** (`src/orchestrator/graph.py`): `run_agent_graph()` is a plain async function that loops over a fixed `PIPELINE` list of 7 sync agent functions (`src/agents/`), calling each via `asyncio.to_thread()` and broadcasting WebSocket progress between steps. Each agent reads a shared `AgentState` (TypedDict) dict and returns a partial dict merged back into it. `decision_agent` synthesizes all analyses into predictions, impact, and recommendations. Powered by Google Gemini (`src/agents/gemini_client.py`), which automatically falls back to OpenRouter/Nemotron (`src/ai/planner.py`) when Gemini fails (e.g. free-tier `429 RESOURCE_EXHAUSTED`).
- **v2 — event-driven multi-agent runtime** (`src/runtime/`): a `Planner` (`planner.py`) decomposes a goal into a dependency-aware task DAG (`state.py`'s `TaskSpec`/`TaskState`); a `Scheduler` (`scheduler.py` — unrelated to `src/scheduler/main.py` below, despite the name) executes ready tasks concurrently in dependency waves via workers (`workers.py` — several wrap the *same* v1 agent functions from `src/agents/`); `Reflection` (`reflection.py`) reviews worker confidence and can request a deeper re-pass; `Decision` (`decision.py`) synthesizes the result; `Workflow` (`workflow.py`) gates on human approval before executing notify/create-incident/store-memory steps. All transitions publish events on an async pub/sub bus (`event_bus.py`), bridged to the frontend as `runtime_event` over the same WebSocket the v1 pipeline uses. `engine.py`'s `RuntimeEngine` (`submit_goal()`, `wait_for()`, `resolve()`) is the single entry point, exposed via `src/api/routes/runtime.py`.

Both pipelines write to the same `agent_decisions` table and are reachable from the same FastAPI app — v1 via `POST /api/chat` / `POST /api/simulate`, v2 via `POST /api/goal`.

### Data Flow

```
External APIs (Open-Meteo, OpenAQ)
    → Pipelines (weather/aqi/feedback) — fetch & save raw data per district
    → CityScoreService — derives traffic/environment/risk scores from latest readings
    → Scheduled every 15 min via APScheduler (src/scheduler/main.py, and again
      in-process by src/main.py's lifespan() — see the double-run note above)

User query → POST /api/chat or /api/simulate → run_agent_graph() (v1, see above)
User goal  → POST /api/goal → RuntimeEngine.submit_goal() (v2, see above)
```

### Backend Structure

- **`src/main.py`** — FastAPI app; mounts all routers; starts an in-process APScheduler for the 15-min pipelines (and registers the weekly knowledge refresh alongside them) in `lifespan()`; CORS is currently wide open (`allow_origins=["*"]`)
- **`src/orchestrator/graph.py`** — v1 pipeline runner (`run_agent_graph()`); see "Two Coexisting Agent Pipelines" above
- **`src/agents/`** — One file per v1 agent node; all agents receive `AgentState` (TypedDict) and return a partial dict to merge back into state; several are also called directly by v2 workers (`src/runtime/workers.py`)
- **`src/runtime/`** — v2 event-driven runtime: `engine.py` (entry point), `planner.py`, `scheduler.py` (task-wave scheduler), `workers.py`, `reflection.py`, `decision.py`, `workflow.py`, `state.py`, `event_bus.py`, `memory.py` (Qdrant-backed knowledge search + Neo4j-backed decision-chain storage, both with automatic in-memory/keyword fallback when unconfigured), `monitor.py`
- **`src/ai/`** — AI Gateway: `gateway.py` (`call_openrouter()`, the single choke point for all OpenRouter/Nemotron calls, using a per-request `aiohttp.ClientTimeout` set from `settings.openrouter_timeout_seconds`), `planner.py` (safety-wrapped completion), `embedding.py`, `reranker.py`, `safety.py` (content-safety check, fails open). All inactive by default — every function degrades to `None`/passthrough when `OPENROUTER_API_KEY` is unset
- **`src/knowledge_pipeline/`** — RAG ingestion: `bootstrap.py` (one-shot: OSM + Wikidata + Wikipedia + Government PDF + GeoJSON → Neo4j + Qdrant `city_knowledge` collection), `scheduler.py` (weekly Wikipedia-only refresh job — re-collects, re-chunks, and idempotently re-upserts into `city_knowledge`; registered on the same APScheduler instance(s) as the 15-min pipelines in both `src/scheduler/main.py` and `src/main.py`'s `lifespan()`; gated behind a Gemini or OpenRouter key, otherwise skipped with a log line), `collectors/`, `loaders/`, `parsers/`, `processors/`, `config/pdf_sources.yaml` (now seeded with real Vietnamese government PDF sources — AQI, traffic-safety, disaster-response, and public-health documents)
- **`src/crawlers/`** — `crawl_service.py`, `news_crawler.py`; wired into `POST /api/crawl` (`src/api/routes/simulation_v2.py`)
- **`src/simulation/`** — `engine.py`, `profiles.py`; the v2 what-if simulator, exposed via `src/api/routes/simulation_v2.py` (`/api/simulation/start|stop|status|scenarios`) — distinct from the v1 simulator below
- **`src/ws/manager.py`** — WebSocket connection manager shared by both pipelines and `src/api/routes/ws.py`
- **`src/api/routes/`** — FastAPI routers: `chat`, `simulator` (v1), `districts`, `scores`, `timeline`, `aqi`, `decisions`, `runtime` (v2 goal/run/approval endpoints), `simulation_v2`, `ws`
- **`src/pipelines/`** — `WeatherPipeline`, `AQIPipeline`, `FeedbackPipeline` — each fetches external data and writes to DB for all districts
- **`src/services/city_score_service.py`** — Derives the four scores (traffic, environment, citizen, risk, overall) from latest weather+AQI
- **`src/repositories/`** — Thin async SQLAlchemy helpers (`get_latest`, `get_all`, `get_recent`, batched `save_all`)
- **`src/models/`** — SQLAlchemy ORM models (mapped to PostgreSQL tables)
- **`src/schemas/`** — Pydantic v2 schemas for API I/O
- **`src/utils/config.py`** — `Settings` via pydantic-settings; see Environment Variables below for the full field list

### Simulator

Two separate simulators exist:
- **v1** — `POST /api/simulate` accepts a scenario name (`heavy_rain`, `air_pollution`, `major_event`, `heatwave`). The `SCENARIOS` dict in `src/api/routes/simulator.py` maps each to `rain_multiplier` and `aqi_boost` values that override weather/AQI data before `run_agent_graph()` runs.
- **v2** — `src/simulation/engine.py` + `profiles.py`, exposed via `src/api/routes/simulation_v2.py`.

### Frontend Structure

- **`src/App.tsx`** — No router. Local `useState` toggles between two full-page views: `CommandCenterPage` ("Command Center", v1 UI) and `MissionControlPage` ("Mission Control v2", v2 runtime UI)
- **`src/services/api.ts`** — Single `axios` instance with empty `baseURL`; Vite dev proxy forwards `/api/*` to `localhost:8000`
- **`src/types/index.ts`** — All shared TypeScript interfaces, spanning both pipelines: v1 (`District`, `CityScore`, `DecisionOut`, `AgentDecisionOut`, `SimulationScenario`, `AQIPoint`) and v2 (`RuntimeRun`, `RuntimeTask`, `RuntimeDecision`, `RuntimeEvidence`, `WorkflowStep`, `TimelineEntry`, `SimulationStatus`, `ScenarioInfo`, `CrawlResults`, `RuntimeMonitor`)
- **Active pages**: `CommandCenterPage.tsx` (imports `HanoiMap`, `AgentGraph`, `SimulatorModal`), `MissionControlPage.tsx` (imports `SimulationPanel`)
- **Active components**: `HanoiMap`, `AgentGraph`, `SimulatorModal`, `SimulationPanel`, plus `ScoreGauge`, `DistrictCard`, `AlertBanner`, `DecisionPanel`
- **Unused legacy pages** — `DashboardPage.tsx`, `MapPage.tsx`, `CopilotPage.tsx`, `SimulatorPage.tsx`, `RiskRadarPage.tsx`, `TimelinePage.tsx` still exist under `src/pages/` but are not imported by `App.tsx` or any active page — dead code from an earlier router-based version of the app. Confirm with `grep -rn "DashboardPage\|MapPage\|CopilotPage\|SimulatorPage\|RiskRadarPage\|TimelinePage" frontend/src/App.tsx frontend/src/pages/CommandCenterPage.tsx frontend/src/pages/MissionControlPage.tsx` before assuming any of them are reachable.
- **`src/hooks/useWebSocket.ts`** — auto-reconnecting WebSocket hook, used by both active pages

### Database

PostgreSQL schema is in `docker/postgres/init.sql` — seeded with 12 Hanoi districts. Tables: `cities`, `districts`, `weather`, `aqi`, `events`, `citizen_feedback`, `city_score`, `agent_decisions`. All have a `city_id` column defaulting to `'hanoi'`. Neo4j (entity/relation graph) and Qdrant (vector search) are separate, optional stores configured via `NEO4J_*`/`QDRANT_*` env vars — every integration point falls back to an in-memory/keyword implementation when they're unset.

### Testing

Tests use SQLite in-memory via the `db_session` fixture in `tests/conftest.py`, which overrides the `get_db` FastAPI dependency. `pytest.ini` sets `asyncio_mode = auto` — all test functions can be `async` without explicit markers. Test directories mirror `src/`: `test_agents/`, `test_ai/`, `test_api/`, `test_knowledge_pipeline/`, `test_pipelines/`, `test_repositories/`, `test_runtime/`, `test_services/`, plus `test_health.py`, `test_integration.py`, `test_models.py`.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` for prod, `sqlite+aiosqlite:///:memory:` in tests |
| `GEMINI_API_KEY` | Yes | Google Gemini API key, used by the v1 pipeline and knowledge-pipeline entity extraction |
| `OPENROUTER_API_KEY` | No | Enables the AI Gateway (`src/ai/`) — NVIDIA Nemotron planning/embedding/rerank/safety, and the Gemini-quota fallback path (`src/agents/gemini_client.py`). Every AI Gateway function degrades to `None`/passthrough when unset |
| `OPENROUTER_TIMEOUT_SECONDS` | No | Per-request timeout for `call_openrouter()` (default `10.0`) |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | No | Decision-chain memory (`src/runtime/memory.py`) and the knowledge graph (`src/knowledge_pipeline/loaders/neo4j_loader.py`). Falls back to an in-memory chain list when `NEO4J_URI` is unset |
| `QDRANT_URL` / `QDRANT_API_KEY` | No | Knowledge search (`src/runtime/memory.py`) and the `city_knowledge` collection (`src/knowledge_pipeline/loaders/qdrant_loader.py`). Falls back to static keyword search over SOP docs when `QDRANT_URL` is unset |
| `CHROMADB_HOST` / `CHROMADB_PORT` | No | Declared in `Settings` but not read anywhere else in `backend/src` — legacy, superseded by Qdrant. Safe to leave unset |
