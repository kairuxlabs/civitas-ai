# Civitas AI — Urban Operating System for Hanoi

An AI-powered urban intelligence platform that ingests real-time environmental data, runs a multi-agent LangGraph pipeline, and provides city operators with actionable insights through a modern React dashboard.

---

## Overview

Civitas AI monitors 12 Hanoi districts in real time by pulling weather and air quality data every 15 minutes, then running it through a 6-agent LangGraph pipeline (powered by Google Gemini) to produce risk scores, predictions, and recommendations. Operators interact with the system through a web dashboard featuring live maps, radar charts, an AI copilot chat, and a what-if scenario simulator.

---

## Screenshots

| Dashboard | Risk Radar | AI Copilot |
|-----------|-----------|------------|
| Score gauges, AQI trend chart, district table | Radar chart + AI recommendation + timeline | Real-time chat with agent decisions |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, MapLibre GL, TanStack Query |
| **Backend** | FastAPI, LangGraph, LangChain (Google Gemini), SQLAlchemy (async) |
| **Database** | PostgreSQL 15, ChromaDB (vector store) |
| **Scheduler** | APScheduler — runs full pipeline every 15 minutes |
| **Data Sources** | Open-Meteo (weather), OpenAQ (air quality) |
| **Infrastructure** | Docker Compose |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  Dashboard · Map · Risk Radar · Copilot · Simulator · Timeline│
└────────────────────────┬────────────────────────────────────┘
                         │ /api/*  (Vite proxy → :8000)
┌────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                         │
│  /api/districts  /api/scores  /api/chat  /api/simulate       │
│  /api/timeline   /api/aqi/history                           │
└────┬───────────────────────────┬────────────────────────────┘
     │                           │
┌────▼────────────┐   ┌──────────▼───────────────────────────┐
│   PostgreSQL    │   │       LangGraph Pipeline               │
│  districts      │   │  traffic → environment → event →      │
│  weather / aqi  │   │  citizen → decision → explanation     │
│  city_score     │   │  (Google Gemini via LangChain)        │
│  agent_decisions│   └──────────────────────────────────────┘
└─────────────────┘
         ▲
┌────────┴────────────────────────────────────────────────────┐
│                    APScheduler (every 15 min)                │
│  WeatherPipeline → AQIPipeline → FeedbackPipeline           │
│  → CityScoreService (per district)                          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Pipeline

Each chat/simulation request runs a 6-node LangGraph graph:

```
traffic_agent → environment_agent → event_agent
    → citizen_agent → decision_agent → explanation_agent
```

Every agent receives the full `AgentState` (weather data, AQI data, events, feedback) and appends its analysis. `decision_agent` synthesises all analyses into predictions, impact assessment, and recommendations. Results are persisted to `agent_decisions`.

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Quick Start (Docker)

```bash
git clone https://github.com/kairus-dev/civitas-ai.git
cd civitas-ai

# Set your Gemini key
echo "GEMINI_API_KEY=your_key_here" > .env

docker-compose up
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Adminer (DB UI) | http://localhost:8080 |

### Local Development

**Backend**

```bash
cd backend
cp .env.example .env        # fill in DATABASE_URL and GEMINI_API_KEY

pip install -r requirements.txt

# Requires PostgreSQL + ChromaDB running (see docker-compose.yml)
uvicorn src.main:app --reload --port 8000

# Run the scheduler in a separate terminal
python -m src.scheduler.main
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/districts` | List all 12 Hanoi districts |
| `GET` | `/api/scores` | Latest city scores for all districts |
| `GET` | `/api/scores/{district_id}` | Score for a single district |
| `POST` | `/api/chat` | Send a query to the AI agent pipeline |
| `POST` | `/api/simulate` | Run a what-if scenario |
| `GET` | `/api/timeline` | Recent agent decisions (paginated) |
| `GET` | `/api/aqi/history/{district_id}` | AQI trend data (last N readings) |

**Chat request body:**
```json
{ "query": "Tình hình ngập lụt tại quận này?", "district_id": 3 }
```

**Simulate request body:**
```json
{ "scenario": "heavy_rain", "district_id": 3 }
```

Available scenarios: `heavy_rain` · `air_pollution` · `major_event` · `heatwave`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | — |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `CHROMADB_HOST` | ChromaDB host | `localhost` |
| `CHROMADB_PORT` | ChromaDB port | `8001` |

---

## Project Structure

```
civitas-ai/
├── backend/
│   ├── src/
│   │   ├── agents/          # 6 LangGraph agent nodes
│   │   ├── api/routes/      # FastAPI routers
│   │   ├── orchestrator/    # LangGraph graph builder + runner
│   │   ├── pipelines/       # Weather, AQI, Feedback data fetchers
│   │   ├── repositories/    # Async SQLAlchemy data access
│   │   ├── services/        # CityScoreService
│   │   ├── scheduler/       # APScheduler entry point
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 I/O schemas
│   │   └── utils/           # Config (pydantic-settings), logger
│   └── tests/               # pytest async tests (SQLite in-memory)
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Map, Copilot, Simulator, RiskRadar, Timeline
│       ├── components/      # ScoreGauge, DistrictCard, AlertBanner, DecisionPanel
│       ├── services/api.ts  # Axios client
│       └── types/index.ts   # Shared TypeScript interfaces
├── docker/
│   └── postgres/init.sql    # Schema + 12 Hanoi district seed data
└── docker-compose.yml
```

---

## Running Tests

```bash
cd backend

# All tests (uses SQLite in-memory — no external services needed)
pytest

# Single file
pytest tests/test_health.py

# Single test
pytest tests/test_health.py::test_health_endpoint
```

---

## Database Schema

The PostgreSQL schema (in `docker/postgres/init.sql`) is automatically applied on first start. Key tables:

| Table | Description |
|---|---|
| `districts` | 12 Hanoi districts with GeoJSON metadata |
| `weather` | Timestamped temperature, humidity, rain, wind per district |
| `aqi` | PM2.5, PM10, CO, NO₂, AQI index per district |
| `city_score` | Derived traffic, environment, citizen, risk, overall scores |
| `agent_decisions` | Full LangGraph pipeline output (predictions, impact, recommendations) |

---

## License

MIT
