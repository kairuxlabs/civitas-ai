import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import DecisionWorkspacePage from '../../pages/stitch/DecisionWorkspacePage'
import { api } from '../../services/api'
import type { RuntimeMonitor, RuntimeRun } from '../../types'
import { LanguageProvider } from '../../i18n/LanguageContext'

function renderPage() {
  return renderWithQueryClient(<LanguageProvider><DecisionWorkspacePage /></LanguageProvider>)
}

vi.mock('../../services/api')

const monitor: RuntimeMonitor = {
  agents: {},
  active_runs: 0,
  total_runs: 0,
}

const submittedRun: RuntimeRun = {
  run_id: 'run-1',
  goal: 'Reduce congestion',
  district_id: 1,
  status: 'awaiting_approval',
  tasks: [],
  timeline: [],
  workflow_steps: [],
  decision: {
    risk: 'medium',
    confidence: 70,
    summary: 'Reroute traffic',
    prediction: 'Congestion down',
    recommendation: ['Close flooded roads'],
    evidence: [],
  },
  created_at: '2026-07-21T09:00:00Z',
  decision_record_id: null,
  reflection: null,
}

const activeRun: RuntimeRun = {
  ...submittedRun,
  tasks: [{
    id: 't1',
    agent: 'planner',
    depends_on: [],
    priority: 1,
    status: 'done',
    attempts: 1,
    result: null,
    error: null,
    started_at: '2026-07-21T09:00:00Z',
    finished_at: '2026-07-21T09:00:10Z',
    latency_ms: 10,
  }],
}

const simStatusIdle = {
  running: false,
  scenario: 'normal',
  scenario_label: 'Normal',
  interval_s: 30,
  auto_goal: true,
  tick: 0,
  values: { rain: 0, aqi: 90, temperature: 30, humidity: 70, wind_speed: 10 },
  last_auto_goal: null,
}

beforeEach(() => {
  vi.mocked(api.getRuns).mockResolvedValue([])
  vi.mocked(api.getRuntimeMonitor).mockResolvedValue(monitor)
  vi.mocked(api.getScores).mockResolvedValue([])
  vi.mocked(api.submitGoal).mockResolvedValue(submittedRun)
  vi.mocked(api.getRun).mockResolvedValue(activeRun)
  vi.mocked(api.getScenarios).mockResolvedValue([{ name: 'heavy_rain', label: 'Heavy rain' }])
  vi.mocked(api.getSimulationStatus).mockResolvedValue(simStatusIdle)
  vi.mocked(api.startSimulation).mockResolvedValue({ ...simStatusIdle, running: true, tick: 1 })
  vi.mocked(api.stopSimulation).mockResolvedValue(simStatusIdle)
  vi.mocked(api.runCrawl).mockResolvedValue({ weather: { ok: true, count: 5 } })
  vi.mocked(api.getDistricts).mockResolvedValue([{ id: 1, city_id: 'hanoi', name: 'Hoan Kiem' }])
  vi.mocked(api.getAQIHistory).mockResolvedValue([])
})

describe('DecisionWorkspacePage', () => {
  it('submits a goal and shows approve controls', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(api.submitGoal).toHaveBeenCalledWith('Reduce congestion after rain', 1))
    await waitFor(() => expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument())
  })

  it('renders the Digital Twin panel and starts the simulation from its Start button', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('digital-twin-panel')).toBeInTheDocument())
    const startButton = await screen.findByTestId('sim-start-btn')
    await user.click(startButton)

    await waitFor(() => expect(api.startSimulation).toHaveBeenCalled())
  })

  it('renders critic notes and reflection notes when present on the run', async () => {
    const runWithNotes: RuntimeRun = {
      ...activeRun,
      decision: { ...activeRun.decision!, critic_notes: ['Evidence is stale for District 3'] },
      reflection: { avg_confidence: 60, notes: ['Traffic agent reported low confidence'], missing: [] },
    }
    vi.mocked(api.submitGoal).mockResolvedValue(runWithNotes)
    vi.mocked(api.getRun).mockResolvedValue(runWithNotes)

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getByTestId('decision-critic-notes')).toBeInTheDocument())
    expect(screen.getByText('Evidence is stale for District 3')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('decision-reflection-notes')).toBeInTheDocument())
    expect(screen.getByText('Traffic agent reported low confidence')).toBeInTheDocument()
  })

  it('omits critic notes and reflection sections when absent from the run', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument())
    expect(screen.queryByTestId('decision-critic-notes')).not.toBeInTheDocument()
    expect(screen.queryByTestId('decision-reflection-notes')).not.toBeInTheDocument()
  })

  it('shows the real district name and risk level in the mission header once a run is active', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getAllByText('Hoan Kiem').length).toBeGreaterThan(0))
    expect(screen.getByText(/medium risk/i)).toBeInTheDocument()
  })

  it('updates the City Score gauge to the clicked district\'s overall score', async () => {
    vi.mocked(api.getDistricts).mockResolvedValue([
      { id: 1, city_id: 'hanoi', name: 'Hoan Kiem' },
      { id: 2, city_id: 'hanoi', name: 'Ba Dinh' },
    ])
    vi.mocked(api.getScores).mockResolvedValue([
      { id: 1, city_id: 'hanoi', district_id: 1, timestamp: '2026-07-21T09:00:00Z', traffic_score: 40, environment_score: 90, citizen_score: 70, risk_score: 20, overall_score: 60 },
      { id: 2, city_id: 'hanoi', district_id: 2, timestamp: '2026-07-21T09:00:00Z', traffic_score: 80, environment_score: 50, citizen_score: 60, risk_score: 10, overall_score: 90 },
    ])
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('city-score-value')).toHaveTextContent('60'))

    await user.click(screen.getByTestId('district-2'))

    await waitFor(() => expect(screen.getByTestId('city-score-value')).toHaveTextContent('90'))
    expect(screen.getByText('Ba Dinh')).toBeInTheDocument()
  })

  it('switching the map metric toggle re-renders the map with the selected metric', async () => {
    vi.mocked(api.getScores).mockResolvedValue([
      { id: 1, city_id: 'hanoi', district_id: 1, timestamp: '2026-07-21T09:00:00Z', traffic_score: 40, environment_score: 90, citizen_score: 70, risk_score: 20, overall_score: 60 },
    ])
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('map-metric-toggle')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: 'Traffic' }))

    await waitFor(() => expect(screen.getAllByText('40').length).toBeGreaterThan(0))
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    localStorage.setItem('civitas-language', 'vi')
    renderPage()

    await waitFor(() => expect(screen.getByText('Chưa có nhiệm vụ nào đang chạy')).toBeInTheDocument())
    expect(screen.getByPlaceholderText('Giảm ùn tắc sau mưa lớn…')).toBeInTheDocument()
    localStorage.removeItem('civitas-language')
  })

  it('opens the evidence modal when the Evidence tile is clicked, and closes it via the close button', async () => {
    const runWithEvidence: RuntimeRun = {
      ...activeRun,
      decision: {
        ...activeRun.decision!,
        evidence: [
          { agent: 'traffic', source: 'Open-Meteo', type: 'sensor', content: 'Rain 45mm/h driving congestion risk', confidence: 0.9, time: '2026-07-21T08:00:00Z' },
          { agent: 'knowledge', source: 'SOP', type: 'sop', content: 'Flood Emergency SOP: activate drainage pumps.', confidence: 0.85, time: 'static' },
        ],
      },
    }
    vi.mocked(api.submitGoal).mockResolvedValue(runWithEvidence)
    vi.mocked(api.getRun).mockResolvedValue(runWithEvidence)

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getByTestId('decision-evidence-toggle')).toBeInTheDocument())
    expect(screen.queryByTestId('decision-evidence-modal')).not.toBeInTheDocument()

    await user.click(screen.getByTestId('decision-evidence-toggle'))

    await waitFor(() => expect(screen.getByTestId('decision-evidence-modal')).toBeInTheDocument())
    const evidenceList = screen.getByTestId('decision-evidence-list')
    expect(evidenceList).toHaveTextContent('Rain 45mm/h driving congestion risk')
    expect(evidenceList).toHaveTextContent('Flood Emergency SOP: activate drainage pumps.')
    expect(evidenceList).toHaveTextContent('Open-Meteo')
    expect(evidenceList).toHaveTextContent('90%')

    await user.click(screen.getByRole('button', { name: 'Close' }))
    await waitFor(() => expect(screen.queryByTestId('decision-evidence-modal')).not.toBeInTheDocument())
  })

  it('closes the evidence modal when the Escape key is pressed', async () => {
    const runWithEvidence: RuntimeRun = {
      ...activeRun,
      decision: {
        ...activeRun.decision!,
        evidence: [
          { agent: 'traffic', source: 'Open-Meteo', type: 'sensor', content: 'Rain driving congestion risk', confidence: 0.9, time: '2026-07-21T08:00:00Z' },
        ],
      },
    }
    vi.mocked(api.submitGoal).mockResolvedValue(runWithEvidence)
    vi.mocked(api.getRun).mockResolvedValue(runWithEvidence)

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getByTestId('decision-evidence-toggle')).toBeInTheDocument())
    await user.click(screen.getByTestId('decision-evidence-toggle'))
    await waitFor(() => expect(screen.getByTestId('decision-evidence-modal')).toBeInTheDocument())

    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByTestId('decision-evidence-modal')).not.toBeInTheDocument())
  })

  it('keeps the Execution Trace list in a bounded, scrollable container regardless of task count', async () => {
    const manyTasksRun: RuntimeRun = {
      ...activeRun,
      tasks: Array.from({ length: 15 }, (_, i) => ({
        id: `t${i}`,
        agent: `worker-${i}`,
        depends_on: [],
        priority: 1,
        status: 'done' as const,
        attempts: 1,
        result: null,
        error: null,
        started_at: '2026-07-21T09:00:00Z',
        finished_at: '2026-07-21T09:00:10Z',
        latency_ms: 10,
      })),
    }
    vi.mocked(api.submitGoal).mockResolvedValue(manyTasksRun)
    vi.mocked(api.getRun).mockResolvedValue(manyTasksRun)

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(screen.getByText(/worker-14/)).toBeInTheDocument())
    // All 15 tasks render in the DOM (not truncated) inside a height-bounded,
    // independently scrollable container — the page itself never grows tall.
    const taskList = screen.getByText(/worker-0$/).closest('ul')!
    expect(taskList.className).toContain('max-h-72')
    expect(taskList.className).toContain('overflow-y-auto')
  })
})
