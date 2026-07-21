# Stitch UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the App top-tab toggle with a Stitch Mission Control shell (sidebar + design tokens + React Router), wire Overview / Decision Workspace / Decision Sessions to existing APIs, wrap Command Center unchanged, and ship mock layouts for the remaining nav screens.

**Architecture:** `AppShell` provides fixed sidebar + `<Outlet />`. New pages port structure from `docs/ui/stitch_civitas_ai_decision_platform/*/code.html` using Tailwind tokens from `civitas_intelligence/DESIGN.md`. Decision Workspace reuses Mission Control API/polling patterns; Decision Sessions reuses `DecisionSessionsPanel` data layer. No new backend routes.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind 3, react-router-dom 6 (already in package.json), TanStack Query, lucide-react, existing `api.ts` / Vitest / Playwright.

## Global Constraints

- Work only in worktree `worktree-decision-session-knowledge-quality` (Decision Session + Knowledge Quality APIs already present).
- UI copy is English (match Stitch).
- `/` = Platform Overview; no Landing page in phase 1.
- Do not restyle Command Center internals — wrap only.
- Do not depend on Stitch CDN background images; reuse `HanoiMap` or district lists.
- Prefer `lucide-react` icons over Material Symbols.
- Commit messages: short, professional, **no** `Co-Authored-By` / `Co-authored-by` trailers (CLAUDE.md). If the environment injects a trailer, strip it before finishing the task.
- Preserve existing `data-testid`s on Decision Sessions / EvidenceModal; extend `docs/TESTING.md` when adding new ids.
- Follow CLAUDE.md test commands: backend needs `DATABASE_URL` + `GEMINI_API_KEY`; frontend via Vite proxy (no hardcoded API origin).

**Spec:** `docs/superpowers/specs/2026-07-21-stitch-ui-shell-design.md`

**Stitch sources:** `docs/ui/stitch_civitas_ai_decision_platform/` (may live on main checkout; read from repo root or main path if missing in worktree).

---

### Task 1: Design tokens + fonts

**Files:**
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Produces: Tailwind color/spacing/font tokens matching Stitch `DESIGN.md` (`primary`, `secondary`, `tertiary`, `surface-*`, `outline*`, `background`, `on-surface*`).

- [ ] **Step 1: Replace `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // keep legacy aliases used by Command Center
        accent: '#3B82F6',
        danger: '#EF4444',
        warning: '#F59E0B',
        success: '#10B981',
        // Stitch Civitas Intelligence tokens
        background: '#10131a',
        surface: '#10131a',
        'surface-dim': '#10131a',
        'surface-bright': '#363941',
        'surface-container-lowest': '#0b0e15',
        'surface-container-low': '#191b23',
        'surface-container': '#1d2027',
        'surface-container-high': '#272a31',
        'surface-container-highest': '#32353c',
        'surface-variant': '#32353c',
        'on-surface': '#e1e2ec',
        'on-surface-variant': '#c2c6d6',
        'on-background': '#e1e2ec',
        outline: '#8c909f',
        'outline-variant': '#424754',
        primary: '#adc6ff',
        'on-primary': '#002e6a',
        'primary-container': '#4d8eff',
        'on-primary-container': '#00285d',
        secondary: '#4edea3',
        'on-secondary': '#003824',
        'secondary-container': '#00a572',
        'on-secondary-container': '#00311f',
        tertiary: '#ffb786',
        'on-tertiary': '#502400',
        'tertiary-container': '#df7412',
        error: '#ffb4ab',
        'on-error': '#690005',
        'error-container': '#93000a',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      spacing: {
        unit: '4px',
        gutter: '16px',
        'margin-desktop': '24px',
        'container-padding': '20px',
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 2: Update `frontend/index.html` fonts + title**

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
    <title>Civitas AI — Decision Intelligence</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Update `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-background text-on-surface font-sans antialiased;
}

@layer components {
  .glass-panel {
    @apply bg-surface-container/80 border border-outline-variant/60;
  }
}
```

- [ ] **Step 4: Typecheck tokens load**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS (no errors from config; TS ignores tailwind config)

- [ ] **Step 5: Commit**

```bash
git add frontend/tailwind.config.js frontend/index.html frontend/src/index.css
git commit -m "feat(frontend): add Stitch design tokens and fonts"
```

Strip any auto-injected `Co-authored-by` trailer before leaving the task.

---

### Task 2: AppShell + React Router skeleton

**Files:**
- Create: `frontend/src/layout/AppShell.tsx`
- Create: `frontend/src/pages/stitch/MockStitchPage.tsx`
- Create: `frontend/src/pages/stitch/OverviewPage.tsx` (placeholder)
- Create: `frontend/src/pages/stitch/DecisionWorkspacePage.tsx` (placeholder)
- Create: `frontend/src/pages/stitch/DecisionSessionsPage.tsx` (placeholder)
- Create: `frontend/src/pages/stitch/CommandCenterRoute.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/__tests__/layout/AppShell.test.tsx`

**Interfaces:**
- Produces: routes `/`, `/workspace`, `/sessions`, `/command-center`, `/data-sources`, `/knowledge`, `/intelligence`, `/reports`, `/settings`.
- Consumes: `react-router-dom` (`BrowserRouter`, `Routes`, `Route`, `NavLink`, `Outlet`, `Navigate`).

- [ ] **Step 1: Write failing AppShell nav test**

```tsx
// frontend/src/__tests__/layout/AppShell.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import AppShell from '../../layout/AppShell'

describe('AppShell', () => {
  it('renders sidebar nav links for phase-1 routes', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<div>Overview outlet</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Workspace' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Sessions' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Command Center' })).toBeInTheDocument()
    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test — expect fail**

Run: `cd frontend && npx vitest run src/__tests__/layout/AppShell.test.tsx`
Expected: FAIL — cannot find `AppShell`

- [ ] **Step 3: Implement `AppShell.tsx`**

```tsx
// frontend/src/layout/AppShell.tsx
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, LineChart, History, Terminal, Database, Share2,
  Building2, FileBarChart, Settings, Rocket,
} from 'lucide-react'

const NAV: { to: string; label: string; icon: typeof LayoutDashboard; end?: boolean }[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/workspace', label: 'Decision Workspace', icon: LineChart },
  { to: '/sessions', label: 'Decision Sessions', icon: History },
  { to: '/command-center', label: 'Command Center', icon: Terminal },
  { to: '/data-sources', label: 'Data Sources', icon: Database },
  { to: '/knowledge', label: 'Knowledge Graph', icon: Share2 },
  { to: '/intelligence', label: 'City Intelligence', icon: Building2 },
  { to: '/reports', label: 'Reports', icon: FileBarChart },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function navClass({ isActive }: { isActive: boolean }) {
  return [
    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
    isActive
      ? 'bg-secondary-container/20 text-secondary border-r-2 border-secondary font-semibold'
      : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest',
  ].join(' ')
}

export default function AppShell() {
  const navigate = useNavigate()
  return (
    <div data-testid="app-shell" className="min-h-screen bg-background text-on-surface">
      <aside className="h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col z-50">
        <div className="px-6 py-5">
          <div className="text-xl font-bold text-primary">Civitas AI</div>
          <div className="text-[10px] text-on-surface-variant mt-0.5">Hanoi City System Operator</div>
        </div>
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={navClass}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-outline-variant">
          <button
            type="button"
            onClick={() => navigate('/workspace')}
            className="w-full bg-primary text-on-primary font-semibold py-2.5 rounded-lg hover:brightness-110 transition flex items-center justify-center gap-2 text-sm"
          >
            <Rocket size={16} /> Run Decision
          </button>
          <p className="text-[10px] text-secondary flex items-center gap-1.5 mt-3 px-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            AI Runtime: Active
          </p>
        </div>
      </aside>
      <div className="ml-64 min-h-screen flex flex-col">
        <main className="flex-1 min-h-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Placeholder pages + Command Center wrap + `App.tsx`**

```tsx
// frontend/src/pages/stitch/MockStitchPage.tsx
export default function MockStitchPage({ title, blurb }: { title: string; blurb: string }) {
  return (
    <div className="p-margin-desktop space-y-4" data-testid="mock-stitch-page">
      <h1 className="text-2xl font-bold text-on-surface">{title}</h1>
      <p className="text-sm text-on-surface-variant max-w-2xl">{blurb}</p>
      <div className="glass-panel rounded-xl p-6 text-sm text-on-surface-variant">
        Layout preview — live data wiring comes in a later phase.
      </div>
    </div>
  )
}
```

```tsx
// frontend/src/pages/stitch/OverviewPage.tsx
export default function OverviewPage() {
  return <div className="p-6 text-on-surface-variant" data-testid="overview-page">Overview placeholder</div>
}
```

```tsx
// frontend/src/pages/stitch/DecisionWorkspacePage.tsx
export default function DecisionWorkspacePage() {
  return <div className="p-6" data-testid="decision-workspace-page">Workspace placeholder</div>
}
```

```tsx
// frontend/src/pages/stitch/DecisionSessionsPage.tsx
export default function DecisionSessionsPage() {
  return <div className="p-6" data-testid="decision-sessions-page">Sessions placeholder</div>
}
```

```tsx
// frontend/src/pages/stitch/CommandCenterRoute.tsx
import CommandCenterPage from '../CommandCenterPage'

export default function CommandCenterRoute() {
  return (
    <div data-testid="command-center-route" className="h-full min-h-screen">
      <CommandCenterPage />
    </div>
  )
}
```

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from './layout/AppShell'
import OverviewPage from './pages/stitch/OverviewPage'
import DecisionWorkspacePage from './pages/stitch/DecisionWorkspacePage'
import DecisionSessionsPage from './pages/stitch/DecisionSessionsPage'
import CommandCenterRoute from './pages/stitch/CommandCenterRoute'
import MockStitchPage from './pages/stitch/MockStitchPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15000, retry: 1 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #424754; border-radius: 10px; }
        * { box-sizing: border-box; }
        html, body, #root { height: 100%; margin: 0; padding: 0; }
      `}</style>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<OverviewPage />} />
            <Route path="workspace" element={<DecisionWorkspacePage />} />
            <Route path="sessions" element={<DecisionSessionsPage />} />
            <Route path="command-center" element={<CommandCenterRoute />} />
            <Route path="data-sources" element={<MockStitchPage title="Data Sources" blurb="Ingestion health and pipeline status (mock)." />} />
            <Route path="knowledge" element={<MockStitchPage title="Knowledge Graph" blurb="Neo4j entity explorer (mock layout)." />} />
            <Route path="intelligence" element={<MockStitchPage title="City Intelligence" blurb="District score deep-dive (mock layout)." />} />
            <Route path="reports" element={<MockStitchPage title="Reports" blurb="Decision report archive (mock layout)." />} />
            <Route path="settings" element={<MockStitchPage title="Settings" blurb="Platform configuration (mock layout)." />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 5: Run AppShell test + unit suite subset**

Run: `cd frontend && npx vitest run src/__tests__/layout/AppShell.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/layout/AppShell.tsx frontend/src/pages/stitch frontend/src/App.tsx frontend/src/__tests__/layout/AppShell.test.tsx
git commit -m "feat(frontend): add Stitch AppShell and React Router routes"
```

---

### Task 3: Overview page + health API helper

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/pages/stitch/OverviewPage.tsx`
- Test: `frontend/src/__tests__/pages/OverviewPage.test.tsx`

**Interfaces:**
- Produces: `api.getHealth(): Promise<{ status: string }>`
- Consumes: `api.getScores()`, `api.getDistricts()`, `api.getDecisionSessionAnalytics()`, `HanoiMap`

- [ ] **Step 1: Add `getHealth` to `api.ts`**

Inside `export const api = { ... }`, after `getScores`:

```ts
  getHealth: () => http.get<{ status: string }>('/health').then(r => r.data),
```

- [ ] **Step 2: Write failing Overview test**

```tsx
// frontend/src/__tests__/pages/OverviewPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import OverviewPage from '../../pages/stitch/OverviewPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

beforeEach(() => {
  vi.mocked(api.getHealth).mockResolvedValue({ status: 'ok' })
  vi.mocked(api.getDistricts).mockResolvedValue([
    { id: 1, city_id: 'hanoi', name: 'Hoan Kiem' },
  ])
  vi.mocked(api.getScores).mockResolvedValue([
    {
      id: 1, city_id: 'hanoi', district_id: 1, timestamp: '2026-07-21T09:00:00Z',
      traffic_score: 70, environment_score: 65, citizen_score: 80, risk_score: 20, overall_score: 74,
    },
  ])
  vi.mocked(api.getDecisionSessionAnalytics).mockResolvedValue({
    total_sessions: 3, approval_rate: 50, evaluated_count: 1,
    improved_rate: 100, avg_improvement: 5, avg_decision_latency_minutes: 4,
  })
})

describe('OverviewPage', () => {
  it('renders city score KPI from scores API', async () => {
    renderWithQueryClient(<OverviewPage />)
    await waitFor(() => expect(screen.getByTestId('overview-page')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByTestId('overview-overall-score')).toHaveTextContent('74'))
  })
})
```

- [ ] **Step 3: Run test — expect fail**

Run: `cd frontend && npx vitest run src/__tests__/pages/OverviewPage.test.tsx`
Expected: FAIL on missing `overview-overall-score`

- [ ] **Step 4: Implement `OverviewPage.tsx`**

```tsx
// frontend/src/pages/stitch/OverviewPage.tsx
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Activity, Database, Rocket, ShieldAlert } from 'lucide-react'
import { api } from '../../services/api'
import HanoiMap from '../../components/HanoiMap'

export default function OverviewPage() {
  const navigate = useNavigate()
  const [selectedDistrict, setSelectedDistrict] = useState(1)

  const { data: health } = useQuery({ queryKey: ['health'], queryFn: api.getHealth, refetchInterval: 15000 })
  const { data: districts } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 15000 })
  const { data: analytics } = useQuery({
    queryKey: ['decision-sessions-analytics'],
    queryFn: api.getDecisionSessionAnalytics,
    refetchInterval: 10000,
  })

  const avgOverall = useMemo(() => {
    if (!scores?.length) return null
    return Math.round(scores.reduce((s, x) => s + x.overall_score, 0) / scores.length)
  }, [scores])

  return (
    <div data-testid="overview-page" className="p-margin-desktop space-y-gutter pb-16">
      <section className="glass-panel p-6 rounded-xl relative overflow-hidden">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight mb-2">City Status Matrix</h1>
            <p className="text-on-surface-variant max-w-xl text-sm">
              Hanoi Metropolitan Area. {(districts?.length ?? 12)} districts reporting
              {health?.status ? ` · API ${health.status}` : ''}.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/workspace')}
            className="bg-primary text-on-primary text-sm font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shrink-0"
          >
            <Rocket size={16} /> Run Decision
          </button>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-primary">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Overall City Score</span>
            <Activity size={16} className="text-primary" />
          </div>
          <div data-testid="overview-overall-score" className="text-2xl font-semibold">
            {avgOverall ?? '—'}
            <span className="text-sm text-on-surface-variant font-normal"> / 100</span>
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-secondary">
          <div className="text-xs text-on-surface-variant mb-2">Decision Sessions</div>
          <div className="text-2xl font-semibold">{analytics?.total_sessions ?? '—'}</div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-primary-container">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Approval Rate</span>
            <Database size={16} className="text-primary-container" />
          </div>
          <div className="text-2xl font-semibold">
            {analytics?.approval_rate != null ? `${analytics.approval_rate}%` : '—'}
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-tertiary">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Improved Rate</span>
            <ShieldAlert size={16} className="text-tertiary" />
          </div>
          <div className="text-2xl font-semibold">
            {analytics?.improved_rate != null ? `${analytics.improved_rate}%` : '—'}
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-xl overflow-hidden">
        <div className="p-4 border-b border-outline-variant flex items-center justify-between">
          <h2 className="font-semibold text-base">Live Intelligence Stream: Hanoi</h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-primary/30 text-primary bg-primary/10">
            LIVE TELEMETRY
          </span>
        </div>
        <div className="p-4 bg-surface-container-lowest">
          <HanoiMap
            scores={scores ?? []}
            selectedId={selectedDistrict}
            onSelect={setSelectedDistrict}
          />
        </div>
      </section>
    </div>
  )
}
```

If `HanoiMap` prop names differ, read `frontend/src/components/HanoiMap.tsx` and adapt — do not invent props.

- [ ] **Step 5: Run Overview test**

Run: `cd frontend && npx vitest run src/__tests__/pages/OverviewPage.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/pages/stitch/OverviewPage.tsx frontend/src/__tests__/pages/OverviewPage.test.tsx
git commit -m "feat(frontend): wire Stitch Overview page to scores and health APIs"
```

---

### Task 4: Decision Workspace page (runtime integration)

**Files:**
- Modify: `frontend/src/pages/stitch/DecisionWorkspacePage.tsx`
- Test: `frontend/src/__tests__/pages/DecisionWorkspacePage.test.tsx`
- Reference only: `frontend/src/pages/MissionControlPage.tsx` (copy polling/mutation patterns; English labels)

**Interfaces:**
- Consumes: `api.submitGoal`, `api.getRun`, `api.getRuns`, `api.resolveRun`, `api.getRuntimeMonitor`, `api.getScores`, `HanoiMap`

- [ ] **Step 1: Write failing workspace test**

```tsx
// frontend/src/__tests__/pages/DecisionWorkspacePage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import DecisionWorkspacePage from '../../pages/stitch/DecisionWorkspacePage'
import { api } from '../../services/api'

vi.mock('../../services/api')

beforeEach(() => {
  vi.mocked(api.getRuns).mockResolvedValue([])
  vi.mocked(api.getRuntimeMonitor).mockResolvedValue({ agents: {}, active_runs: 0, total_runs: 0 } as never)
  vi.mocked(api.getScores).mockResolvedValue([])
  vi.mocked(api.submitGoal).mockResolvedValue({
    run_id: 'run-1', goal: 'Reduce congestion', status: 'awaiting_approval',
    district_id: 1, tasks: [], timeline: [], workflow_steps: [], decision: {
      risk: 'medium', confidence: 70, summary: 'Reroute traffic', prediction: 'congestion down',
      recommendation: ['Close flooded roads'], evidence: [],
    },
  } as never)
  vi.mocked(api.getRun).mockResolvedValue({
    run_id: 'run-1', goal: 'Reduce congestion', status: 'awaiting_approval',
    district_id: 1, tasks: [
      { id: 't1', agent: 'planner', status: 'done', depends_on: [], latency_ms: 10 },
    ], timeline: [], workflow_steps: [], decision: {
      risk: 'medium', confidence: 70, summary: 'Reroute traffic', prediction: 'congestion down',
      recommendation: ['Close flooded roads'], evidence: [],
    },
  } as never)
})

describe('DecisionWorkspacePage', () => {
  it('submits a goal and shows approve controls', async () => {
    renderWithQueryClient(<DecisionWorkspacePage />)
    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    const input = screen.getByPlaceholderText(/Reduce congestion/i)
    await userEvent.type(input, 'Reduce congestion after rain')
    await userEvent.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))
    await waitFor(() => expect(api.submitGoal).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument())
  })
})
```

Adjust mocks to match exact `RuntimeRun` / monitor types in `frontend/src/types/index.ts` if the cast fails typecheck — read the types and make fields complete.

- [ ] **Step 2: Run test — expect fail**

Run: `cd frontend && npx vitest run src/__tests__/pages/DecisionWorkspacePage.test.tsx`
Expected: FAIL (placeholder page)

- [ ] **Step 3: Implement workspace page**

Port Mission Control logic into Stitch layout:

```tsx
// frontend/src/pages/stitch/DecisionWorkspacePage.tsx
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, Brain, CheckCircle, Loader2, Rocket, XCircle, AlertTriangle,
} from 'lucide-react'
import { api } from '../../services/api'
import HanoiMap from '../../components/HanoiMap'
import type { RuntimeRun, RuntimeTask } from '../../types'

const GOAL_PRESETS = [
  'Prepare the city for heavy rain tonight',
  'Respond to severe air pollution tomorrow',
  'Ensure safety for the weekend festival at Hoan Kiem',
]

const ACTIVE_STATUSES = new Set(['planning', 'running', 'reflecting', 'deciding', 'executing_workflow'])

export default function DecisionWorkspacePage() {
  const [goal, setGoal] = useState('')
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [selectedDistrict, setSelectedDistrict] = useState(1)
  const queryClient = useQueryClient()

  const { data: run } = useQuery({
    queryKey: ['v2-run', activeRunId],
    queryFn: () => api.getRun(activeRunId!),
    enabled: !!activeRunId,
    refetchInterval: q => {
      const status = q.state.data?.status
      return status && ACTIVE_STATUSES.has(status) ? 1200 : status === 'awaiting_approval' ? 4000 : false
    },
  })

  const { data: runs } = useQuery({ queryKey: ['v2-runs'], queryFn: api.getRuns, refetchInterval: 5000 })
  const { data: scores } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 15000 })

  const submit = useMutation({
    mutationFn: (g: string) => api.submitGoal(g, selectedDistrict),
    onSuccess: r => {
      setActiveRunId(r.run_id)
      queryClient.invalidateQueries({ queryKey: ['v2-runs'] })
      queryClient.invalidateQueries({ queryKey: ['decision-sessions'] })
    },
  })

  const resolve = useMutation({
    mutationFn: (approved: boolean) => api.resolveRun(activeRunId!, approved),
    onSuccess: r => {
      queryClient.setQueryData(['v2-run', activeRunId], r)
      queryClient.invalidateQueries({ queryKey: ['decision-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['decision-sessions-analytics'] })
    },
  })

  const avgOverall = useMemo(() => {
    if (!scores?.length) return null
    return Math.round(scores.reduce((s, x) => s + x.overall_score, 0) / scores.length)
  }, [scores])

  const selectedScore = scores?.find(s => s.district_id === selectedDistrict)

  return (
    <div data-testid="decision-workspace-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
        <div className="space-y-2 flex-1">
          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant">
            {run ? `Active run: ${run.run_id}` : 'No active mission'}
          </p>
          <h1 className="text-2xl font-bold tracking-tight">
            {run?.goal ?? 'Decision Workspace'}
          </h1>
          <div className="flex flex-wrap gap-2">
            <input
              value={goal}
              onChange={e => setGoal(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && goal.trim().length >= 3 && submit.mutate(goal.trim())}
              placeholder="Reduce congestion after heavy rain…"
              className="flex-1 min-w-[240px] bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
            <button
              type="button"
              disabled={goal.trim().length < 3 || submit.isPending}
              onClick={() => submit.mutate(goal.trim())}
              className="bg-primary text-on-primary font-semibold text-sm px-4 py-2 rounded-lg disabled:opacity-40 flex items-center gap-2"
            >
              {submit.isPending ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
              Execute Decision
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {GOAL_PRESETS.map(p => (
              <button
                key={p}
                type="button"
                onClick={() => { setGoal(p); submit.mutate(p) }}
                className="text-xs bg-surface-container-high hover:bg-surface-bright border border-outline-variant text-on-surface-variant px-2.5 py-1 rounded-full"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        {/* Execution Trace */}
        <section className="xl:col-span-3 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2 text-sm">
              <Activity size={16} className="text-primary" /> Execution Trace
            </h2>
            {run && ACTIVE_STATUSES.has(run.status) && (
              <span className="text-[10px] text-secondary border border-secondary/30 bg-secondary/10 px-2 py-0.5 rounded-full">Live</span>
            )}
          </div>
          <ul className="space-y-3">
            {(run?.tasks ?? []).map((t: RuntimeTask) => (
              <li key={t.id} className="flex gap-2 text-xs">
                {t.status === 'done' ? <CheckCircle size={14} className="text-primary shrink-0" />
                  : t.status === 'failed' ? <AlertTriangle size={14} className="text-tertiary shrink-0" />
                  : t.status === 'running' ? <Loader2 size={14} className="text-primary animate-spin shrink-0" />
                  : <span className="w-3.5 h-3.5 rounded-full border border-outline-variant shrink-0" />}
                <div>
                  <div className="font-semibold text-on-surface">{t.agent}</div>
                  <div className="text-on-surface-variant">{t.status}{t.latency_ms != null ? ` · ${Math.round(t.latency_ms)}ms` : ''}</div>
                </div>
              </li>
            ))}
            {!run?.tasks?.length && (
              <li className="text-xs text-on-surface-variant italic">Submit a goal to start the runtime trace.</li>
            )}
          </ul>
          {(runs ?? []).length > 0 && (
            <div className="pt-3 border-t border-outline-variant space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
              <p className="text-[10px] uppercase text-on-surface-variant">Recent runs</p>
              {runs!.map(r => (
                <button
                  key={r.run_id}
                  type="button"
                  onClick={() => setActiveRunId(r.run_id)}
                  className={`w-full text-left text-xs rounded px-2 py-1.5 ${r.run_id === activeRunId ? 'bg-surface-container-highest text-on-surface' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
                >
                  <div className="truncate">{r.goal}</div>
                  <div className="text-[10px] opacity-70">{r.status}</div>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Map */}
        <section className="xl:col-span-5 glass-panel rounded-xl overflow-hidden">
          <div className="p-3 border-b border-outline-variant text-sm font-semibold">District map</div>
          <div className="p-3 bg-surface-container-lowest">
            <HanoiMap scores={scores ?? []} selectedId={selectedDistrict} onSelect={setSelectedDistrict} />
          </div>
          {selectedScore && (
            <div className="grid grid-cols-2 gap-2 p-3 border-t border-outline-variant text-xs">
              <div>Traffic <span className="font-mono text-on-surface">{Math.round(selectedScore.traffic_score)}</span></div>
              <div>Environment <span className="font-mono text-on-surface">{Math.round(selectedScore.environment_score)}</span></div>
              <div>Risk <span className="font-mono text-on-surface">{Math.round(selectedScore.risk_score)}</span></div>
              <div>Overall <span className="font-mono text-on-surface">{Math.round(selectedScore.overall_score)}</span></div>
            </div>
          )}
        </section>

        {/* Decision + score */}
        <section className="xl:col-span-4 space-y-gutter">
          <div className="glass-panel rounded-xl p-4">
            <div className="text-xs text-on-surface-variant mb-2">City Score</div>
            <div className="text-3xl font-semibold">{avgOverall ?? '—'}<span className="text-sm text-on-surface-variant"> / 100</span></div>
          </div>

          {run?.decision ? (
            <div className="glass-panel rounded-xl p-4 space-y-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Brain size={16} className="text-primary" /> Runtime Decision
              </h3>
              <p className="text-sm text-on-surface-variant">{run.decision.summary}</p>
              <ul className="space-y-1">
                {run.decision.recommendation.map((r, i) => (
                  <li key={i} className="text-xs text-on-surface">• {r}</li>
                ))}
              </ul>
              <div className="text-xs text-on-surface-variant">Confidence: {Math.round(run.decision.confidence)}%</div>
              {run.status === 'awaiting_approval' && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(true)}
                    className="flex-1 bg-secondary-container text-on-secondary-container text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <CheckCircle size={14} /> Approve
                  </button>
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(false)}
                    className="flex-1 bg-error-container/40 text-error text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <XCircle size={14} /> Reject
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel rounded-xl p-4 text-xs text-on-surface-variant italic">
              Decision card appears when the runtime finishes planning.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
```

Read `HanoiMap` props and `RuntimeRun.decision` field names from types; fix compile errors before committing.

- [ ] **Step 4: Run workspace test + tsc**

Run: `cd frontend && npx vitest run src/__tests__/pages/DecisionWorkspacePage.test.tsx && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/stitch/DecisionWorkspacePage.tsx frontend/src/__tests__/pages/DecisionWorkspacePage.test.tsx
git commit -m "feat(frontend): add Stitch Decision Workspace wired to v2 runtime"
```

---

### Task 5: Decision Sessions page (Stitch chrome + English)

**Files:**
- Modify: `frontend/src/pages/stitch/DecisionSessionsPage.tsx`
- Modify: `frontend/src/components/DecisionSessionsPanel.tsx` (English labels + Stitch token classes; keep testids)
- Test: existing `frontend/src/__tests__/components/DecisionSessionsPanel.test.tsx` must stay green

**Interfaces:**
- Consumes: existing panel API hooks; page adds Stitch page header only.

- [ ] **Step 1: Run existing panel tests (baseline)**

Run: `cd frontend && npx vitest run src/__tests__/components/DecisionSessionsPanel.test.tsx`
Expected: PASS before edits

- [ ] **Step 2: English + token restyle in `DecisionSessionsPanel.tsx`**

Replace Vietnamese `STATUS_LABEL` / empty copy with English:

```ts
const STATUS_LABEL: Record<string, string> = {
  collecting: 'Collecting', analyzing: 'Analyzing', recommend: 'Recommend',
  awaiting_approval: 'Awaiting approval', rejected: 'Rejected',
  observing: 'Observing', evaluated: 'Evaluated',
}
```

```tsx
<p className="text-xs text-on-surface-variant italic text-center py-4">No decision sessions yet</p>
```

Swap `bg-slate-*` / `border-slate-*` / `text-slate-*` / cyan accents for Stitch tokens (`bg-surface-container`, `border-outline-variant`, `text-on-surface`, `text-primary`, `bg-primary` for the observe button) without removing `data-testid` attributes.

Update `fmtTime` to `en-US` or `en-GB`.

- [ ] **Step 3: Page wrapper**

```tsx
// frontend/src/pages/stitch/DecisionSessionsPage.tsx
import DecisionSessionsPanel from '../../components/DecisionSessionsPanel'

export default function DecisionSessionsPage() {
  return (
    <div data-testid="decision-sessions-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Decision Sessions</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Track goal lifecycle from submission through observed CityScore outcomes.
        </p>
      </div>
      <DecisionSessionsPanel />
    </div>
  )
}
```

- [ ] **Step 4: Re-run panel tests**

Run: `cd frontend && npx vitest run src/__tests__/components/DecisionSessionsPanel.test.tsx`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/stitch/DecisionSessionsPage.tsx frontend/src/components/DecisionSessionsPanel.tsx
git commit -m "feat(frontend): restyle Decision Sessions page with Stitch shell"
```

---

### Task 6: Mock pages polish + remove duplicate panel from MissionControl

**Files:**
- Modify: `frontend/src/pages/stitch/MockStitchPage.tsx` (optional richer layout)
- Modify: `frontend/src/pages/MissionControlPage.tsx` — remove `<DecisionSessionsPanel />` so sessions live only at `/sessions` (avoids duplicate polling); keep file otherwise for reference
- Verify Command Center route still mounts page

- [ ] **Step 1: Enrich mock page**

```tsx
// frontend/src/pages/stitch/MockStitchPage.tsx
export default function MockStitchPage({ title, blurb }: { title: string; blurb: string }) {
  return (
    <div className="p-margin-desktop space-y-4" data-testid="mock-stitch-page">
      <h1 className="text-2xl font-bold text-on-surface">{title}</h1>
      <p className="text-sm text-on-surface-variant max-w-2xl">{blurb}</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
        {['Signals', 'Coverage', 'Notes'].map(label => (
          <div key={label} className="glass-panel rounded-xl p-4">
            <p className="text-xs text-on-surface-variant mb-2">{label}</p>
            <p className="text-sm text-on-surface">Mock content for phase 1 layout.</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Remove DecisionSessionsPanel from MissionControlPage**

Delete the `DecisionSessionsPanel` import and `<DecisionSessionsPanel />` usage from `MissionControlPage.tsx`. Update `MissionControlPage.test.tsx` if it asserted the panel — remove or retarget that assertion to avoid failures.

- [ ] **Step 3: Run page tests that may break**

Run: `cd frontend && npx vitest run src/__tests__/pages/MissionControlPage.test.tsx src/__tests__/layout/AppShell.test.tsx`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/stitch/MockStitchPage.tsx frontend/src/pages/MissionControlPage.tsx frontend/src/__tests__/pages/MissionControlPage.test.tsx
git commit -m "feat(frontend): polish mock Stitch pages and dedupe sessions panel"
```

---

### Task 7: E2E helpers for shell navigation

**Files:**
- Modify: `frontend/e2e/helpers.ts`
- Modify: `frontend/e2e/06-mission-control.spec.ts`
- Modify: `frontend/e2e/01-layout.spec.ts` only if assertions require old "CityOS Mission Control" / top tabs

**Interfaces:**
- Produces: `switchToMissionControl(page)` navigates to `/workspace` via sidebar (or `page.goto('/workspace')`) instead of clicking removed top tab.
- `waitForApp` still lands on `/` (Overview). Overview may not show "Hoàn Kiếm" — update wait condition to `data-testid="app-shell"` and/or Overview content.

- [ ] **Step 1: Update `waitForApp`**

```ts
export async function waitForApp(page: Page) {
  await page.route('**/api/districts', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DISTRICTS) })
  )
  await page.route('**/api/scores', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SCORES) })
  )
  await page.route('**/health', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  )
  await page.route('**/api/decision-sessions', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  )
  await page.route('**/api/decision-sessions/analytics', route =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        total_sessions: 0, approval_rate: null, evaluated_count: 0,
        improved_rate: null, avg_improvement: null, avg_decision_latency_minutes: null,
      }),
    })
  )
  await page.goto('/')
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('overview-page')).toBeVisible({ timeout: 8_000 })
}
```

- [ ] **Step 2: Update `switchToMissionControl`**

```ts
export async function switchToMissionControl(page: Page) {
  await page.route('**/api/v2/runs', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ runs: [] }) })
  )
  await page.route('**/api/v2/monitor', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ agents: {}, active_runs: 0, total_runs: 0 }) })
  )
  await page.route('**/api/v2/simulation/scenarios', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ scenarios: [{ name: 'heavy_rain', label: 'Heavy rain' }] }) })
  )
  await page.route('**/api/v2/simulation/status', route =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        running: false, scenario: 'normal', scenario_label: 'Normal', interval_s: 30, auto_goal: true, tick: 0,
        values: { rain: 0, aqi: 90, temperature: 30, humidity: 70, wind_speed: 10 }, last_auto_goal: null,
      }),
    })
  )
  await page.goto('/workspace')
  await expect(page.getByTestId('decision-workspace-page')).toBeVisible({ timeout: 8_000 })
  await expect(page.getByPlaceholder(/Reduce congestion/i)).toBeVisible()
}
```

- [ ] **Step 3: Fix suite 01 / 06 assertions**

- `01-layout.spec.ts`: stop requiring `CityOS Mission Control` text / Command Center-only chrome if Overview shell differs. Prefer `app-shell` + Overview heading/`overview-page`. Keep district map assertions only on routes that still render them (Overview or Command Center).
- `06-mission-control.spec.ts`: Decision Sessions test should `page.goto('/sessions')` (or click sidebar **Decision Sessions**) and assert `decision-session-card`. Goal submit tests use English placeholder/buttons from Workspace.

- [ ] **Step 4: Run mocked E2E (01-04, 06)**

Run: `cd frontend && npx playwright test e2e/01-layout.spec.ts e2e/02-map-interaction.spec.ts e2e/03-simulator.spec.ts e2e/04-chat.spec.ts e2e/06-mission-control.spec.ts`
Expected: PASS (or only pre-existing unrelated flakes). Suite 05 excluded here.

Note: suites 01–04 currently assume Command Center at `/`. After shell change, either:
- point those suites at `/command-center` via `page.goto('/command-center')` inside a small helper, **or**
- keep Command Center quirks working under Overview only where map/chat exist.

**Required resolution for this task:** Command Center E2E suites (01–04) must navigate to `/command-center` after mocks, because chat/simulator live on Command Center, not Overview. Add:

```ts
export async function waitForCommandCenter(page: Page) {
  await waitForApp(page)
  await page.goto('/command-center')
  await expect(page.getByTestId('command-center-route')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('app-header')).toBeVisible({ timeout: 15_000 })
}
```

Update 01–04 to use `waitForCommandCenter` instead of `waitForApp` where they need Command Center UI. Keep `waitForApp` for Overview-level checks if any.

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/
git commit -m "test(e2e): navigate Stitch shell routes for Mission Control suites"
```

---

### Task 8: Full verification + TESTING.md touch-up

**Files:**
- Modify: `docs/TESTING.md` if new testids/`AppShell` paths need listing
- No feature code unless fixes required

- [ ] **Step 1: Frontend unit + tsc**

Run: `cd frontend && npx tsc --noEmit && npm test`
Expected: PASS (all Vitest)

- [ ] **Step 2: Backend smoke (runtime still green)**

Run: `cd backend` with `DATABASE_URL` + `GEMINI_API_KEY` set, then:
`pytest tests/test_api/test_decision_sessions.py tests/test_runtime/ -q`
Expected: PASS

- [ ] **Step 3: Optional docs line for AppShell testid**

Add to `docs/TESTING.md` data-testid table if missing:

| App shell | `app-shell` |
| Overview page | `overview-page` |
| Decision Workspace | `decision-workspace-page` |
| Decision Sessions page | `decision-sessions-page` |
| Command Center route wrap | `command-center-route` |
| Mock Stitch page | `mock-stitch-page` |

- [ ] **Step 4: Commit if docs changed**

```bash
git add docs/TESTING.md
git commit -m "docs: add Stitch shell testids to TESTING.md"
```

---

## Plan self-review

1. **Spec coverage:** Shell/tokens (T1), routes/shell (T2), Overview+health (T3), Workspace (T4), Sessions (T5), mocks+CC wrap (T2/T6), E2E (T7), verify (T8). Non-goals (Landing, new backends) excluded.
2. **Placeholders:** None intentional; HanoiMap props must be read from source during T3/T4.
3. **Types:** Use `frontend/src/types/index.ts` `RuntimeRun` / `DecisionSessionAnalytics` as source of truth when mocks complain.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-21-stitch-ui-shell.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Which approach?
