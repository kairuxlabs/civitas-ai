import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import DecisionWorkspacePage from '../../pages/stitch/DecisionWorkspacePage'
import { api } from '../../services/api'
import type { RuntimeMonitor, RuntimeRun } from '../../types'

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

beforeEach(() => {
  vi.mocked(api.getRuns).mockResolvedValue([])
  vi.mocked(api.getRuntimeMonitor).mockResolvedValue(monitor)
  vi.mocked(api.getScores).mockResolvedValue([])
  vi.mocked(api.submitGoal).mockResolvedValue(submittedRun)
  vi.mocked(api.getRun).mockResolvedValue(activeRun)
})

describe('DecisionWorkspacePage', () => {
  it('submits a goal and shows approve controls', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(<DecisionWorkspacePage />)

    await waitFor(() => expect(screen.getByTestId('decision-workspace-page')).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Reduce congestion/i), 'Reduce congestion after rain')
    await user.click(screen.getByRole('button', { name: /Execute Decision|Submit|Run/i }))

    await waitFor(() => expect(api.submitGoal).toHaveBeenCalledWith('Reduce congestion after rain', 1))
    await waitFor(() => expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument())
  })
})
