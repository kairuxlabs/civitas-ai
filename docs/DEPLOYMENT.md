# Deployment Guide

Civitas AI (CityOS v2) deploys across three managed cloud services, plus two optional knowledge-layer services:

| Service | Role | Platform | Required |
|---|---|---|---|
| **Neon.tech** | PostgreSQL database | Serverless Postgres | ✅ |
| **Render** | FastAPI backend + v2 runtime | Docker container | ✅ |
| **Vercel** | React frontend | Static + CDN | ✅ |
| **Neo4j Aura** | Decision memory graph | Free tier | Optional |
| **Qdrant Cloud** | SOP vector search | Free tier | Optional |

The optional services power the v2 knowledge layer. When their env vars are unset the backend degrades gracefully to in-memory fallbacks — the whole platform works without them.

GitHub Actions orchestrates the pipeline: tests run on every push, deploys trigger on `main` only.

---

## 1. Neon.tech (Database)

### Create a database

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project — choose region **Singapore** (closest to Render's Singapore region)
3. On the project dashboard, copy the **Connection string** — it looks like:
   ```
   postgresql://user:password@ep-xxx-yyy.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Modify the scheme for asyncpg:
   ```
   postgresql+asyncpg://user:password@ep-xxx-yyy.ap-southeast-1.aws.neon.tech/neondb?ssl=require
   ```

### Run the migration

From the `backend/` directory, run the one-time migration script to create all tables and seed the 12 Hanoi districts:

```bash
cd backend
DATABASE_URL="postgresql+asyncpg://user:password@..." python -m scripts.migrate_neon
```

Expected output:
```
Connecting to: postgresql+asyncpg://user:password@ep...
Creating tables...
Seeded 12 districts.
Migration complete.
```

This is idempotent — if run again on an already-seeded database, it skips the seed step.

**If your Neon database was provisioned before 2026-07-18**, it is missing two indexes added since (`idx_events_district_start`, `idx_citizen_feedback_district_created`). Add them once via `psql` or the Neon SQL editor:

```sql
CREATE INDEX IF NOT EXISTS idx_events_district_start ON events(district_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_citizen_feedback_district_created ON citizen_feedback(district_id, created_at DESC);
```

**If your Neon database was provisioned before 2026-07-20**, it is also missing the `evidence` column on `agent_decisions`. Add it once via `psql` or the Neon SQL editor:

```sql
ALTER TABLE agent_decisions ADD COLUMN IF NOT EXISTS evidence JSONB;
```

---

## 2. Render (Backend)

### Create a web service

1. Sign up at [render.com](https://render.com)
2. **New → Web Service** → connect your GitHub repository
3. Configure:
   - **Name**: `civitas-ai-backend`
   - **Region**: Singapore
   - **Runtime**: Docker
   - **Dockerfile path**: `./backend/Dockerfile.prod`
   - **Docker Context**: `./backend`
   - **Plan**: Free (or Starter for always-on)

### Set environment variables

In **Environment** tab, add:

| Variable | Required | Value |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` from Neon |
| `GEMINI_API_KEY` | ✅ | Google Gemini key (planner/decision/knowledge fall back to rules without it) |
| `API_KEY` | ❌ | Enables the `X-API-Key` header check on mutating endpoints (decisions approve/reject, decision-session observe, v2 goal/approval, v2 simulation start/stop, v2 crawl). Empty = auth disabled (default) |
| `CORS_ORIGINS` | ❌ | Comma-separated allowed origins. Defaults to the Vite dev server + the deployed Vercel frontend — override if you deploy the frontend to a different domain |
| `OPENROUTER_API_KEY` | ❌ | Enables the AI Gateway (NVIDIA Nemotron planning/embedding/rerank/safety) and the Gemini-quota fallback path. Verify real model slugs with `python -m scripts.verify_openrouter` before depending on this for a demo |
| `OPENROUTER_TIMEOUT_SECONDS` | ❌ | Per-request timeout for OpenRouter calls (default `10.0`) |
| `NEO4J_URI` | ❌ | `neo4j+s://xxx.databases.neo4j.io` from Neo4j Aura — enables the knowledge graph (entity/relation storage + live `find_related()` queries from the Knowledge Agent) and persistent decision-memory |
| `NEO4J_USER` | ❌ | Usually `neo4j` |
| `NEO4J_PASSWORD` | ❌ | From Aura credentials file |
| `QDRANT_URL` | ❌ | `https://xxx.cloud.qdrant.io` — enables vector SOP/`city_knowledge` search |
| `QDRANT_API_KEY` | ❌ | From Qdrant Cloud dashboard |

### Auto-deploy from GitHub

Render deploys automatically on every push to `main` (default **Auto-Deploy: Yes** when the repo is connected). No deploy hook or GitHub secret is needed for the backend — the `deploy-backend` job in `deploy.yml` is informational only.

### Verify deployment

After the first deploy, check the health endpoint and the v2 runtime:

```bash
curl https://civitas-ai-backend.onrender.com/health
# → {"status":"ok","version":"2.0.0"}

# Submit an autonomous goal to the v2 runtime
curl -X POST https://civitas-ai-backend.onrender.com/api/v2/goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "Chuẩn bị thành phố cho trận mưa lớn tối nay", "district_id": 1}'
# → 202 with {"run_id": "...", "status": "planning", ...}

# Poll the run until "awaiting_approval", then approve
curl https://civitas-ai-backend.onrender.com/api/v2/runs/<run_id>
curl -X POST https://civitas-ai-backend.onrender.com/api/v2/runs/<run_id>/approval \
  -H "Content-Type: application/json" -d '{"approved": true}'

# Digital Twin simulation + data crawl
curl -X POST https://civitas-ai-backend.onrender.com/api/v2/simulation/start \
  -H "Content-Type: application/json" -d '{"scenario": "heavy_rain", "interval_s": 30}'
curl https://civitas-ai-backend.onrender.com/api/v2/simulation/status
curl -X POST https://civitas-ai-backend.onrender.com/api/v2/simulation/stop
curl -X POST https://civitas-ai-backend.onrender.com/api/v2/crawl \
  -H "Content-Type: application/json" -d '{"sources": ["weather", "news"]}'
```

The Swagger UI is available at `https://civitas-ai-backend.onrender.com/docs`.

---

## 3. Optional Knowledge Layer (Neo4j Aura + Qdrant Cloud)

Both services are free-tier and optional. Without them:
- Decision memory (Incident → Decision → Workflow → Outcome chains) lives in process memory and resets on redeploy.
- SOP retrieval uses keyword matching over the built-in SOP documents.

### Neo4j Aura

1. Sign up at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura) → create a **Free** instance
2. Download the credentials file when prompted (shown once)
3. Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` on Render

Decision chains are written as `(:Incident)-[:LED_TO]->(:Decision)-[:EXECUTED_AS]->(:Workflow)-[:RESULTED_IN]->(:Outcome)`.

### Qdrant Cloud

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io) → create a free cluster
2. Create a collection named `cityos_sop` and index the SOP documents
3. Set `QDRANT_URL`, `QDRANT_API_KEY` on Render

If the collection is missing or the service is unreachable, the backend logs a warning and falls back to keyword search — requests never fail because of it.

---

## 4. Vercel (Frontend)

### Link your project

```bash
cd frontend
npx vercel login          # authenticate
npx vercel link           # link to a Vercel project (create new or select existing)
cat .vercel/project.json  # shows projectId and orgId
```

### Set environment variables

In the Vercel dashboard under **Settings → Environment Variables**, add:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://civitas-ai-backend.onrender.com` |
| `VITE_WS_URL` | `wss://civitas-ai-backend.onrender.com/ws` |
| `VITE_API_KEY` | Only needed if the backend has `API_KEY` set — attaches `X-API-Key` to every request. Leave unset otherwise |

> ⚠️ Paste values as plain text — a BOM character copied into these values has previously broken API calls in production (the frontend strips a leading BOM defensively, but keep values clean).

### Get GitHub secrets

You need three values from Vercel for the CI/CD pipeline:

```bash
# Token: create at vercel.com/account/tokens
VERCEL_TOKEN=...

# From .vercel/project.json
VERCEL_ORG_ID=...
VERCEL_PROJECT_ID=...
```

### SPA routing

`frontend/vercel.json` is already configured with the rewrite rule that sends all requests to `index.html`:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

## 5. GitHub Actions Setup

### Add repository secrets

In **Settings → Secrets and variables → Actions**, add:

| Secret | Description |
|---|---|
| `VERCEL_TOKEN` | From vercel.com/account/tokens |
| `VERCEL_ORG_ID` | From `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | From `.vercel/project.json` after `vercel link` |

The backend needs no secret: Render auto-deploys from the GitHub push itself.

### Workflow overview

Two workflow files manage the pipeline:

**`.github/workflows/ci.yml`** — runs on every push and pull request:

```
backend tests (pytest, 369 tests)
    └─ SQLite in-memory, no external services needed
       (v2 runtime tests force Gemini/Qdrant/Neo4j fallback paths)

frontend unit tests (Vitest, 110 tests)

frontend E2E tests (Playwright, suites 06–07)
    └─ Chromium, API responses mocked (Decision Workspace, Decision Sessions,
       remaining Stitch screens — no Command Center, it was removed)

frontend build check
    └─ TypeScript + Vite production build
```

All four jobs run in parallel. Deploys are independent of CI (see below).

**`.github/workflows/deploy.yml`** — runs on push to `main` only:

```
deploy-backend  → informational (Render auto-deploys from the GitHub push)
deploy-frontend → vercel deploy --prod → Vercel builds from source and publishes
```

### Deployment flow

```
git push origin main
    │
    ├── ci.yml (parallel)
    │   ├── backend: pytest (369)
    │   ├── frontend-unit: vitest (110)
    │   ├── frontend-e2e: playwright (suites 06-07)
    │   └── frontend-build: npm run build
    │
    ├── Render auto-deploy → new Docker container (triggered by the push itself)
    │
    └── deploy.yml (on main)
        └── vercel deploy --prod → new Vercel deployment
```

---

## 6. Production Docker Image

`backend/Dockerfile.prod` builds a minimal production image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

Key points:
- No `--reload` flag (hot-reload disabled)
- **Exactly 1 Uvicorn worker** — the v2 runtime keeps run state, the simulation engine, and the event bus in process memory. Multiple workers would split that state: a run created on worker A would 404 on worker B, and simulation start/status would disagree between workers. Scale vertically (bigger instance), not horizontally, unless run state is moved to a shared store first.
- Slim base image to minimize image size

---

## 7. Render Blueprint

`render.yaml` at the repo root defines the service declaratively:

1. In Render dashboard: **New → Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates the service
4. Set `DATABASE_URL` and `GEMINI_API_KEY` manually in the dashboard (marked `sync: false`); add the optional `OPENROUTER_API_KEY` / `NEO4J_*` / `QDRANT_*` variables there too if used

---

## Troubleshooting

**Backend returns 502 on Render free plan**

Render free services spin down after inactivity. The first request after ~15 min will cold-start the container (10–30s). Use Render's Starter plan for always-on.

**`GET /api/v2/runs/{id}` returns 404 for a run you just created**

The backend is running more than one worker process — v2 run state is in-memory and per-worker. Ensure the container runs `--workers 1` (see section 6) and that no platform-level replica count > 1 is set.

**Simulation stops by itself on the free plan**

The Digital Twin loop lives inside the web process. When Render spins the free instance down after inactivity, the loop stops and `simulation/status` resets after cold start. Restart it with `POST /api/v2/simulation/start`, or use the Starter plan for continuous simulation. Runs it already triggered are unaffected in Postgres (`agent_decisions`), but in-memory run history resets.

**Auto-goal fires no runs even though simulation is running**

Auto-goal requires `auto_goal: true` on start, values over threshold (rain > 20mm or AQI > 150 — the `normal` scenario never crosses them), and a 5-minute cooldown between triggers. Check `GET /api/v2/simulation/status` → `last_auto_goal`.

**Crawl returns `ok: false` for a source**

Each source fails independently (`weather` = Open-Meteo, `aqi` = OpenAQ, `news` = VnExpress RSS). SSL or rate-limit errors from one provider don't affect the others; the error text is returned per-source in the response.

**Frontend shows "Failed to fetch" errors**

Verify `VITE_API_BASE_URL` in Vercel matches the exact Render service URL (no trailing slash). Check browser DevTools → Network for CORS errors.

**Neon connection timeout**

Neon serverless connections require SSL. Ensure the connection string uses `ssl=require` (for asyncpg: `?ssl=require`).

**GitHub Actions deploy fails — 401 Unauthorized**

`VERCEL_TOKEN` is expired or has insufficient scope. Create a new token at `vercel.com/account/tokens` with "Full Account" scope.
