# Deployment Guide

Civitas AI deploys across three managed cloud services:

| Service | Role | Platform |
|---|---|---|
| **Neon.tech** | PostgreSQL database | Serverless Postgres |
| **Render** | FastAPI backend | Docker container |
| **Vercel** | React frontend | Static + CDN |

GitHub Actions orchestrates the full pipeline: tests run on every push, deploys trigger on `main` only.

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

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` from Neon |
| `GEMINI_API_KEY` | Your Google Gemini key |

### Get the deploy hook

1. Go to **Settings → Deploy Hook**
2. Copy the URL — it looks like `https://api.render.com/deploy/srv-xxx?key=yyy`
3. Save this as GitHub secret `RENDER_DEPLOY_HOOK_URL`

### Verify deployment

After the first deploy, check the health endpoint:
```bash
curl https://civitas-ai-backend.onrender.com/health
# → {"status":"ok","version":"2.0.0"}
```

The Swagger UI is available at `https://civitas-ai-backend.onrender.com/docs`.

---

## 3. Vercel (Frontend)

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

`frontend/vercel.json` is already configured with the rewrite rule that sends all requests to `index.html`, enabling React Router's client-side navigation:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

## 4. GitHub Actions Setup

### Add repository secrets

In **Settings → Secrets and variables → Actions**, add:

| Secret | Description |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | From Render → Service → Settings → Deploy Hook |
| `VERCEL_TOKEN` | From vercel.com/account/tokens |
| `VERCEL_ORG_ID` | From `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | From `.vercel/project.json` after `vercel link` |

### Workflow overview

Two workflow files manage the pipeline:

**`.github/workflows/ci.yml`** — runs on every push and pull request:

```
backend tests (pytest)
    └─ SQLite in-memory, no external services needed

frontend unit tests (Vitest)
    └─ 51 tests, runs isolated

frontend E2E tests (Playwright, suites 01–04)
    └─ Chromium, API responses mocked

frontend build check
    └─ TypeScript + Vite production build
```

All four jobs run in parallel. The deploy workflow only triggers after CI passes.

**`.github/workflows/deploy.yml`** — runs on push to `main` only:

```
deploy-backend  → POST to Render deploy hook → Render pulls Docker image and redeploys
deploy-frontend → vercel deploy --prod        → Vercel builds from source and publishes
```

### Deployment flow

```
git push origin main
    │
    ├── ci.yml (parallel)
    │   ├── backend: pytest
    │   ├── frontend-unit: vitest
    │   ├── frontend-e2e: playwright (suites 01-04)
    │   └── frontend-build: npm run build
    │
    └── deploy.yml (on main, independent of ci.yml)
        ├── Render deploy hook → new Docker container
        └── vercel deploy --prod → new Vercel deployment
```

---

## 5. Production Docker Image

`backend/Dockerfile.prod` builds a minimal production image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Key differences from the local dev setup:
- No `--reload` flag (hot-reload disabled)
- 2 Uvicorn workers for concurrency
- Slim base image to minimize image size

---

## 6. Render Blueprint

`render.yaml` at the repo root is a Render Blueprint that defines the service declaratively. You can use it to provision the service automatically:

1. In Render dashboard: **New → Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates the service
4. Set `DATABASE_URL` and `GEMINI_API_KEY` manually in the dashboard (marked `sync: false` in the blueprint)

---

## Troubleshooting

**Backend returns 502 on Render free plan**

Render free services spin down after inactivity. The first request after ~15 min will cold-start the container (10–30s). Use Render's Starter plan for always-on.

**Frontend shows "Failed to fetch" errors**

Verify `VITE_API_BASE_URL` in Vercel matches the exact Render service URL (no trailing slash). Check browser DevTools → Network for CORS errors.

**Neon connection timeout**

Neon serverless connections require SSL. Ensure the connection string uses `ssl=require` (for asyncpg: `?ssl=require`).

**GitHub Actions deploy fails — 401 Unauthorized**

`VERCEL_TOKEN` is expired or has insufficient scope. Create a new token at `vercel.com/account/tokens` with "Full Account" scope.
