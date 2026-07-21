# Stitch UI Shell — Design Spec

Status: approved (Part 1 + Part 2)
Date: 2026-07-21
Source: `docs/ui/stitch_civitas_ai_decision_platform/` (`civitas_intelligence/DESIGN.md` + screen `code.html` / `screen.png`)

## 1. Goal

Replace the App.tsx Command Center / Mission Control top-tab toggle with a Stitch-aligned Mission Control shell (sidebar + design tokens + React Router). Wire real backend APIs for Overview, Decision Workspace, and Decision Sessions. Keep Command Center as an unmodified page wrapped by the shell. Remaining Stitch screens are layout/mock only in phase 1.

## 2. Decisions already locked

| Topic | Choice |
|---|---|
| Phase 1 scope | Shell + tokens + Overview, Decision Workspace, Decision Sessions (real API) + Command Center (wrap existing) + mock other nav screens |
| Approach | Port Stitch HTML → React; reuse Mission Control hooks/API for Workspace |
| Language | English (match Stitch) |
| Home route | `/` = Platform Overview (no Landing page) |
| Workspace | New page; do not restyle MissionControlPage in place |
| Command Center | Keep current UI; wrap in shell only |
| App nav | Full replace: React Router + Stitch sidebar (no top tabs) |
| Workspace location | Continue on `worktree-decision-session-knowledge-quality` |

## 3. Design tokens

Port from `civitas_intelligence/DESIGN.md` into Tailwind (`frontend/tailwind.config.js` + fonts in `index.html` / CSS):

- Surfaces: `background` `#10131a`, `surface-*` scale, `outline` / `outline-variant`
- Accents: `primary` `#adc6ff`, `primary-container` `#4d8eff`, `secondary` `#4edea3`, `tertiary` `#ffb786`, `error` `#ffb4ab`
- Fonts: Inter (UI), JetBrains Mono (metrics/timestamps)
- Radius/spacing: match DESIGN.md (`rounded` 0.25–1.5rem, 4px unit, 16px gutter)

Icons: prefer existing `lucide-react` mapped to Stitch Material Symbol meanings (no Material Symbols dependency required unless it stays simpler for parity).

## 4. Shell & routing

**Layout:** fixed left sidebar (~256px) + main `<Outlet />`. Optional top bar per page when Stitch HTML includes one.

**Sidebar nav (English):**

1. Overview → `/`
2. Decision Workspace → `/workspace`
3. Decision Sessions → `/sessions`
4. Command Center → `/command-center` (existing UI)
5. Data Sources → `/data-sources` (mock)
6. Knowledge Graph → `/knowledge` (mock)
7. City Intelligence → `/intelligence` (mock)
8. Reports → `/reports` (mock)
9. Settings → `/settings` (mock)

CTA: “Run Decision” / “+ New Decision” → `/workspace`.

`App.tsx`: `BrowserRouter` + shell layout route; remove the Command Center / Mission Control tab bar.

## 5. Screen specs (phase 1)

### 5.1 Platform Overview `/`

- Port structure from `platform_overview/code.html` (hero status, KPI tiles, district/map stream, pipeline/alerts panels).
- **Real data:** `api.getScores()`, `api.getDistricts()`, `GET /health` (add thin `api.getHealth()` if missing).
- KPI ideas: average `overall_score`, district count, active/recent decision-session analytics when available (`api.getDecisionSessionAnalytics()`).
- Map: reuse `HanoiMap` or a district score list — do not depend on Stitch CDN background images.
- Empty/error: degrade gracefully when backend unreachable.

### 5.2 Decision Workspace `/workspace`

- New page ported from `decision_workspace/code.html` (mission header, execution trace, map/env strip, score/quality cards, approve/reject).
- **Real data / logic reused from Mission Control:**
  - `api.submitGoal`, `api.getRun`, `api.getRuns`, `api.resolveRun`, `api.getRuntimeMonitor`
  - Existing run polling patterns from `MissionControlPage.tsx`
- English goal presets and status labels.
- Execution Trace: map `run.tasks` / `run.timeline` into the vertical stepper (agent steps done/running/pending).
- Decision card: show recommendation + Approve/Reject when `awaiting_approval`.
- Keep `MissionControlPage.tsx` in repo for reference; not mounted in the new shell.

### 5.3 Decision Sessions `/sessions`

- Port/restyle from `decision_sessions_history/code.html`.
- Reuse `DecisionSessionsPanel` data layer (`getDecisionSessions`, `getDecisionSessionAnalytics`, `observeDecisionSession`) — either restyle the panel to Stitch tokens or wrap it in a page chrome that matches Stitch.
- English status labels; keep existing `data-testid`s for Vitest/E2E.

### 5.4 Command Center `/command-center`

- Render existing `CommandCenterPage` inside the shell outlet unchanged (no internal restyle).

### 5.5 Mock screens

`/data-sources`, `/knowledge`, `/intelligence`, `/reports`, `/settings`: Stitch-like layout/chrome with static or fixture copy. No new backend endpoints in phase 1. City Intelligence may display live scores later without blocking phase 1.

## 6. Backend integration (existing only)

| UI need | Backend |
|---|---|
| District list / map | `GET /api/districts` |
| Scores / Overview KPIs | `GET /api/scores` |
| Health heartbeat | `GET /health` |
| Submit / poll / approve runs | `POST /api/v2/goal`, `GET /api/v2/runs`, `GET /api/v2/runs/{id}`, `POST /api/v2/runs/{id}/approval`, `GET /api/v2/monitor` |
| Decision sessions | `GET /api/decision-sessions`, `GET /api/decision-sessions/analytics`, `GET /api/decision-sessions/{id}`, `POST /api/decision-sessions/{id}/observe` |

No new backend routes required for phase 1 UI shell. Optional: `api.getHealth()` client helper only.

## 7. Non-goals (phase 1)

- Landing/marketing page
- Pixel-perfect port of every Stitch decorative CDN asset
- Real Knowledge Graph / Settings / Data Sources / Reports backends
- Restyling Command Center internals
- Replacing v1 chat pipeline UX beyond keeping it reachable
- Light theme / theme toggle persistence (header control may be visual-only)

## 8. Testing expectations

- Preserve/adapt Vitest for `DecisionSessionsPanel` and Overview/Workspace smoke where practical
- Update E2E helpers for shell navigation (sidebar) instead of top tabs where suites assume old App nav
- Keep `data-testid` conventions; extend `docs/TESTING.md` if new ids are added
- `npx tsc --noEmit`, `npm test`, and mocked E2E suites must stay green

## 9. Worktree

Implement on `worktree-decision-session-knowledge-quality` so Decision Session and Knowledge Quality APIs are already available.
