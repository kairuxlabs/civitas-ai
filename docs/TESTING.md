# Testing Guide

Civitas AI has three layers of automated testing:

| Layer | Tool | Count | What it covers |
|---|---|---|---|
| **Backend unit** | pytest + httpx | 278 tests | API routes, services, repositories, agents, runtime, reasoning (critic), AI gateway, knowledge pipeline |
| **Frontend unit** | Vitest + Testing Library | 66 tests | React components, hooks, API service |
| **E2E integration** | Playwright (Chromium) | 46 tests | Full UI flows, map interaction, simulator (incl. Before/After comparison), chat, evidence viewer |

---

## Backend Tests

### Running tests

```bash
cd backend

# All tests
pytest

# With verbose output
pytest -v

# Single file
pytest tests/test_health.py

# Single test
pytest tests/test_health.py::test_health_endpoint

# With coverage report
pytest --cov=src --cov-report=term-missing
```

### Environment

Backend tests use **SQLite in-memory** — no PostgreSQL or external services needed. The `conftest.py` fixture:

1. Creates an in-memory SQLite engine
2. Creates all tables via `Base.metadata.create_all`
3. Overrides the FastAPI `get_db` dependency
4. Wraps the app in `httpx.AsyncClient`

Set a dummy `DATABASE_URL` if your shell doesn't have it:

```bash
# PowerShell
$env:DATABASE_URL = "sqlite+aiosqlite:///./test.db"
$env:GEMINI_API_KEY = "dummy"
pytest

# bash
DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=dummy pytest
```

### Test structure

```
backend/tests/
├── conftest.py                        # shared fixtures: db_session, client
├── test_health.py                     # GET /health
├── test_models.py                     # SQLAlchemy model validation
├── test_integration.py                # cross-layer integration
├── test_api/
│   ├── test_districts.py             # GET /api/districts
│   ├── test_decisions.py             # POST /api/decisions/{id}/approve|reject
│   ├── test_runtime_api.py           # v2 goal/run/approval endpoints
│   └── test_simulation_api.py        # v2 Digital Twin start/stop/status
├── test_agents/                       # one file per v1 agent node
│   ├── test_traffic_agent.py
│   ├── test_environment_agent.py
│   ├── test_event_agent.py
│   ├── test_citizen_agent.py
│   ├── test_knowledge_agent.py        # SOP matching, Qdrant chunks, Neo4j graph facts
│   ├── test_decision_agent.py         # evidence collection across all 5 agents
│   ├── test_critic_agent.py           # v1 wiring of the shared evidence critic
│   ├── test_decision_groundedness.py  # decision-quality regression scenarios
│   ├── test_gemini_client.py
│   └── test_orchestrator.py          # graph.run_agent_graph (mocked Gemini)
├── test_reasoning/
│   └── test_critic.py                # shared, pure-function evidence critic (no LLM)
├── test_ai/                           # AI Gateway: gateway, planner, embedding, reranker, safety
├── test_knowledge_pipeline/           # collectors, parsers, loaders (incl. neo4j_loader), processors, bootstrap, scheduler
├── test_runtime/                      # v2 planner, scheduler, workers, reflection, decision, workflow, event_bus, memory, state
├── test_pipelines/
│   ├── test_aqi_pipeline.py
│   └── test_weather_pipeline.py
├── test_repositories/
│   ├── test_base_repos.py            # district, score, weather, aqi repos
│   └── test_event_feedback_repos.py
└── test_services/
    └── test_city_score_service.py    # score arithmetic
```

---

## Frontend Unit Tests

### Running tests

```bash
cd frontend

# Run all tests (single pass)
npm test

# Watch mode (re-runs on file change)
npm run test:watch

# With UI (browser-based test explorer)
npm run test:ui

# Coverage report
npm run test:coverage
```

### Environment

Tests use **Vitest** with `jsdom` environment. Axios is mocked globally via `vi.hoisted()` in `src/__tests__/setup.ts`. TanStack Query is wrapped in a `createWrapper()` helper that creates a fresh `QueryClient` per test with retries disabled.

### Test structure

```
frontend/src/__tests__/
├── setup.ts                          # global mocks (axios, matchMedia, ResizeObserver)
├── components/
│   ├── HanoiMap.test.tsx             # SVG rendering, district nodes, legend items
│   ├── SimulatorModal.test.tsx       # modal open/close, scenario cards, run button, Before/After comparison, evidence click
│   ├── EvidenceModal.test.tsx        # evidence grouped by agent, confidence display, close behavior
│   ├── DecisionPanel.test.tsx        # confidence bar, prediction, recommendations, explanation
│   ├── ScoreGauge.test.tsx
│   └── AgentGraph.test.tsx           # agent node rendering, status indicators
├── hooks/
│   └── useWebSocket.test.ts         # connection, reconnect, message parsing
└── services/
    └── api.test.ts                   # axios calls, base URL, error handling
```

Note: `CommandCenterPage.tsx` and `MissionControlPage.tsx` have no dedicated unit test file — they're verified via the Playwright E2E suites below instead.

**Key pattern — SVG text assertions:**

Legend items in `HanoiMap` are SVG `<text>` elements, not ARIA-accessible text. Use `container.querySelectorAll('text')`:

```ts
const texts = Array.from(container.querySelectorAll('text')).map(t => t.textContent ?? '')
expect(texts.some(t => t.includes('Good'))).toBe(true)
```

---

## E2E Tests (Playwright)

### Prerequisites

Install Playwright browsers (once):

```bash
cd frontend
npx playwright install chromium
```

### Running E2E tests

```bash
cd frontend

# Run all E2E suites (headless)
npm run e2e

# Headed mode (watch the browser)
npm run e2e:headed

# Interactive UI mode
npm run e2e:ui

# Run a specific suite
npx playwright test e2e/01-layout.spec.ts

# Run with trace on failure
npx playwright test --trace on
```

A Vite dev server must be running on port 3000. The Playwright config (`playwright.config.ts`) uses `reuseExistingServer: true` — start the dev server first:

```bash
# Terminal 1
npm run dev

# Terminal 2
npm run e2e
```

### Test suites

| File | Tests | Backend required | Description |
|---|---|---|---|
| `01-layout.spec.ts` | 9 | No | Header, tabs, map SVG, panels, KPI cards |
| `02-map-interaction.spec.ts` | 15 | No | All 12 district nodes, click → info bar update |
| `03-simulator.spec.ts` | 7 | No | Modal open/close, scenarios, Run button state, Before/After comparison |
| `04-chat.spec.ts` | 8 | No | Chat input, Enter key, AI response, report update, evidence modal |
| `05-integration.spec.ts` | 7 | Yes (auto-skip) | Real health check, real districts, real chat, real simulator |

Suites 01–04 mock all API calls via `page.route()` — they work without a running backend. Suite 05 auto-skips if `http://localhost:8000/health` is unreachable.

### API mocking pattern

All mocked tests use the shared `waitForApp()` helper from `e2e/helpers.ts`. Mocks must be registered **before** `page.goto()`:

```ts
import { waitForApp } from './helpers'

test('example', async ({ page }) => {
  await waitForApp(page)      // registers mocks + navigates + waits for data
  await expect(page.getByTestId('app-header')).toBeVisible()
})
```

`waitForApp` mocks:
- `**/api/districts` → 12 Hanoi district objects
- `**/api/scores` → 12 score objects with `overall_score: 72-83`

It then waits for `data-testid="app-header"` and for the text "Hoàn Kiếm" to appear (confirming TanStack Query resolved).

### data-testid reference

All testable elements have `data-testid` attributes:

| Component | `data-testid` |
|---|---|
| Page wrapper | `mission-control` |
| Header bar | `app-header` |
| Connection badge | `connection-status` |
| Chat messages | `chat-messages` |
| Chat input | `chat-input` |
| Send button | `chat-send` |
| Simulator open button | `simulator-btn` |
| Simulator modal | `simulator-modal` |
| Scenario card | `scenario-{key}` (e.g. `scenario-heavy_rain`) |
| Simulator run button | `simulator-run-btn` |
| District node (map) | `district-{id}` (e.g. `district-1`) |

### Playwright config highlights

```ts
// playwright.config.ts
export default defineConfig({
  timeout: 60_000,      // per-test timeout (browser cold start = ~15s)
  retries: 1,           // retry once on failure
  workers: 1,           // serial execution (avoids port conflicts)
  expect: { timeout: 10_000 },    // assertion timeout
  use: { actionTimeout: 10_000 }, // click/type timeout
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,    // skip startup if already running
    timeout: 30_000,
  },
})
```

---

## CI Integration

In GitHub Actions, all three test layers run in parallel on every push:

```yaml
jobs:
  backend:          # pytest --tb=short
  frontend-unit:    # vitest run
  frontend-e2e:     # playwright test (suites 01-04, no backend)
  frontend-build:   # npm run build (TypeScript + Vite)
```

E2E suite 05 (full-stack integration) is excluded from CI because it requires a live backend and database. Run it locally before merging changes that touch the API.

Playwright HTML reports are uploaded as artifacts on test failure:

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: frontend/playwright-report/
```
