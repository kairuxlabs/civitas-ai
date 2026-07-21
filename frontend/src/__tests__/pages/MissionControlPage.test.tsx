import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import type { RuntimeRun, RuntimeRunSummary } from '../../types'

const mockHttp = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))

vi.mock('axios', () => ({
  default: { create: vi.fn(() => mockHttp) },
}))

import MissionControlPage from '../../pages/MissionControlPage'

const MOCK_RUN: RuntimeRun = {
  run_id: 'run-1',
  goal: 'Chuẩn bị mưa lớn',
  district_id: 1,
  status: 'awaiting_approval',
  tasks: [
    { id: 't1', agent: 'traffic', depends_on: [], priority: 1, status: 'done', attempts: 1, result: {}, error: null, started_at: null, finished_at: null, latency_ms: 120 },
    { id: 't2', agent: 'knowledge', depends_on: ['t1'], priority: 1, status: 'done', attempts: 1, result: {}, error: null, started_at: null, finished_at: null, latency_ms: 300 },
  ],
  decision: {
    summary: 'Rủi ro ngập cao',
    prediction: 'Ngập úng khả năng cao',
    risk: 'high',
    recommendation: ['Kích hoạt bơm thoát nước'],
    confidence: 60,
    evidence: [
      { agent: 'traffic', summary: 'Rain 60mm/h', confidence: 0.9 },
      { agent: 'environment', source: 'OpenAQ', type: 'sensor', content: 'AQI 180', confidence: 0.85 },
    ],
  },
  workflow_steps: [{ step: 'notify', detail: 'Đã gửi thông báo', ts: '2026-07-21T00:00:00Z' }],
  timeline: [{ ts: '2026-07-21T00:00:00Z', actor: 'planner', message: 'Kế hoạch đã tạo' }],
  created_at: '2026-07-21T00:00:00Z',
  decision_record_id: 5,
  reflection: { avg_confidence: 0.8, notes: [], missing: [] },
}

const MOCK_RUNS_SUMMARY: RuntimeRunSummary[] = [
  { run_id: 'run-1', goal: 'Chuẩn bị mưa lớn', district_id: 1, status: 'awaiting_approval', created_at: '2026-07-21T00:00:00Z', task_count: 2, confidence: 60 },
]

function mockGet(overrides: { runs?: RuntimeRunSummary[]; run?: RuntimeRun } = {}) {
  mockHttp.get.mockImplementation((url: string) => {
    if (url === '/api/v2/runs') return Promise.resolve({ data: { runs: overrides.runs ?? [] } })
    if (url === '/api/v2/monitor') return Promise.resolve({ data: { agents: {}, active_runs: 0, total_runs: 0 } })
    if (url === '/api/v2/simulation/scenarios') return Promise.resolve({ data: { scenarios: [] } })
    if (url === '/api/v2/simulation/status') {
      return Promise.resolve({
        data: { running: false, scenario: 'normal', scenario_label: 'Bình thường', interval_s: 30, auto_goal: true, tick: 0, values: { rain: 0, aqi: 90, temperature: 30, humidity: 70, wind_speed: 10 }, last_auto_goal: null },
      })
    }
    if (url.startsWith('/api/v2/runs/') && overrides.run) return Promise.resolve({ data: overrides.run })
    return Promise.reject(new Error(`unexpected GET ${url}`))
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('MissionControlPage', () => {
  it('renders the goal input and preset buttons', () => {
    mockGet()
    renderWithQueryClient(<MissionControlPage />)
    expect(screen.getByPlaceholderText(/Chuẩn bị thành phố/)).toBeTruthy()
  })

  it('submits a goal and shows the resulting run status', async () => {
    mockGet({ run: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: MOCK_RUN })
    renderWithQueryClient(<MissionControlPage />)

    fireEvent.change(screen.getByPlaceholderText(/Chuẩn bị thành phố/), { target: { value: 'Chuẩn bị mưa lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Thực thi/ }))

    await waitFor(() => expect(mockHttp.post).toHaveBeenCalledWith('/api/v2/goal', { goal: 'Chuẩn bị mưa lớn', district_id: 1 }))
    await waitFor(() => expect(screen.getByText('Chờ phê duyệt')).toBeTruthy())
  })

  it('renders task nodes in the runtime DAG for the active run', async () => {
    mockGet({ run: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: MOCK_RUN })
    const { container } = renderWithQueryClient(<MissionControlPage />)

    fireEvent.change(screen.getByPlaceholderText(/Chuẩn bị thành phố/), { target: { value: 'Chuẩn bị mưa lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Thực thi/ }))

    await waitFor(() => {
      const texts = Array.from(container.querySelectorAll('text')).map(t => t.textContent ?? '')
      expect(texts).toContain('traffic')
      expect(texts).toContain('knowledge')
    })
  })

  it('approves a run from the DecisionCard and calls the resolve endpoint', async () => {
    mockGet({ run: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: { ...MOCK_RUN, status: 'executing_workflow' } })
    renderWithQueryClient(<MissionControlPage />)

    fireEvent.change(screen.getByPlaceholderText(/Chuẩn bị thành phố/), { target: { value: 'Chuẩn bị mưa lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Thực thi/ }))
    await waitFor(() => expect(screen.getByText('Rủi ro ngập cao')).toBeTruthy())

    fireEvent.click(screen.getByRole('button', { name: /Phê duyệt/ }))
    await waitFor(() => expect(mockHttp.post).toHaveBeenCalledWith('/api/v2/runs/run-1/approval', { approved: true }))
  })

  it('renders both legacy and structured evidence shapes without literal undefined', async () => {
    mockGet({ run: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: MOCK_RUN })
    renderWithQueryClient(<MissionControlPage />)

    fireEvent.change(screen.getByPlaceholderText(/Chuẩn bị thành phố/), { target: { value: 'Chuẩn bị mưa lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Thực thi/ }))
    await waitFor(() => expect(screen.getByText(/Bằng chứng/)).toBeTruthy())

    fireEvent.click(screen.getByText(/Bằng chứng/))
    expect(screen.getByText(/Rain 60mm\/h/)).toBeTruthy()
    expect(screen.getByText(/AQI 180/)).toBeTruthy()
    expect(screen.queryByText(/undefined/)).toBeNull()
  })

  it('renders workflow steps when present', async () => {
    mockGet({ run: MOCK_RUN })
    mockHttp.post.mockResolvedValueOnce({ data: MOCK_RUN })
    renderWithQueryClient(<MissionControlPage />)

    fireEvent.change(screen.getByPlaceholderText(/Chuẩn bị thành phố/), { target: { value: 'Chuẩn bị mưa lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Thực thi/ }))

    await waitFor(() => expect(screen.getByText('Đã gửi thông báo')).toBeTruthy())
  })

  it('lists run history and switches the active run when clicked', async () => {
    mockGet({ runs: MOCK_RUNS_SUMMARY, run: MOCK_RUN })
    renderWithQueryClient(<MissionControlPage />)

    await waitFor(() => expect(screen.getByText('Chuẩn bị mưa lớn')).toBeTruthy())
    fireEvent.click(screen.getByText('Chuẩn bị mưa lớn'))

    await waitFor(() => expect(mockHttp.get).toHaveBeenCalledWith('/api/v2/runs/run-1'))
  })

  it('renders the Digital Twin simulation panel', () => {
    mockGet()
    renderWithQueryClient(<MissionControlPage />)
    expect(screen.getByText('Digital Twin & Data')).toBeTruthy()
  })
})
