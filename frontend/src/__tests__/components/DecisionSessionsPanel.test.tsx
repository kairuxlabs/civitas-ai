import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import DecisionSessionsPanel from '../../components/DecisionSessionsPanel'
import { api } from '../../services/api'
import type { DecisionSession, DecisionSessionAnalytics } from '../../types'
import { LanguageProvider } from '../../i18n/LanguageContext'

function renderPanel() {
  return renderWithQueryClient(<LanguageProvider><DecisionSessionsPanel /></LanguageProvider>)
}

vi.mock('../../services/api', () => ({
  api: {
    getDecisionSessions: vi.fn(),
    getDecisionSessionAnalytics: vi.fn(),
    observeDecisionSession: vi.fn(),
    getDistricts: vi.fn(),
  },
}))

const analytics: DecisionSessionAnalytics = {
  total_sessions: 2, approval_rate: 50, evaluated_count: 1,
  improved_rate: 100, avg_improvement: 13, avg_decision_latency_minutes: 5,
}

const observingSession: DecisionSession = {
  id: 1, run_id: 'run-1', goal: 'Reduce congestion', district_id: 1,
  status: 'observing', decision_id: 10,
  baseline_scores: { traffic_score: 42, environment_score: 60, citizen_score: 70, risk_score: 30, overall_score: 55 },
  expected_outcome: null, observed_scores: null, outcome_delta: null,
  success_rate: null, outcome_status: null, context_snapshot: null, outcome_evidence: null,
  created_at: '2026-07-21T09:00:00Z', approved_at: '2026-07-21T09:05:00Z',
  observed_at: null, evaluated_at: null,
}

const rejectedSession: DecisionSession = {
  ...observingSession, id: 2, run_id: 'run-2', status: 'rejected',
  baseline_scores: null, approved_at: null,
}

beforeEach(() => {
  vi.mocked(api.getDecisionSessions).mockResolvedValue([observingSession, rejectedSession])
  vi.mocked(api.getDecisionSessionAnalytics).mockResolvedValue(analytics)
  vi.mocked(api.getDistricts).mockResolvedValue([
    { id: 1, city_id: 'hanoi', name: 'Hoan Kiem' },
    { id: 2, city_id: 'hanoi', name: 'Ba Dinh' },
  ])
})

describe('DecisionSessionsPanel', () => {
  it('renders the KPI tiles from analytics', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getByTestId('decision-analytics')).toBeInTheDocument())
    expect(screen.getByTestId('decision-analytics')).toHaveTextContent('2')
  })

  it('renders one card per session', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))
  })

  it('lays out session cards in a responsive grid instead of a height-capped scroll box', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))
    const grid = screen.getAllByTestId('decision-session-card')[0].parentElement!
    expect(grid.className).toContain('grid')
    expect(grid.className).not.toContain('max-h-96')
    expect(grid.className).not.toContain('overflow-y-auto')
  })

  it('renders a timeline stepper on each card', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-timeline')).toHaveLength(2))
  })

  it('shows Check Outcome Now only for sessions in observing status', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))
    expect(screen.getAllByTestId('check-outcome-now-button')).toHaveLength(1)
  })

  it('does not render a baseline/observed card for rejected sessions', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))
    const rejectedCard = screen.getByText('run-2').closest('[data-testid="decision-session-card"]')!
    expect(rejectedCard).not.toHaveTextContent('Baseline')
  })

  it('calls observeDecisionSession and refetches when Check Outcome Now is clicked', async () => {
    vi.mocked(api.observeDecisionSession).mockResolvedValue({ ...observingSession, status: 'evaluated' })
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('check-outcome-now-button')).toHaveLength(1))

    await userEvent.click(screen.getByTestId('check-outcome-now-button'))

    await waitFor(() => expect(api.observeDecisionSession).toHaveBeenCalledWith(1))
  })

  it('filters sessions by status using the real session status field', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))

    await userEvent.selectOptions(screen.getByTestId('decision-sessions-status-filter'), 'rejected')

    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(1))
    expect(screen.getByText('run-2')).toBeInTheDocument()
  })

  it('filters sessions by district using the real district_id field', async () => {
    vi.mocked(api.getDecisionSessions).mockResolvedValue([
      observingSession,
      { ...rejectedSession, district_id: 2 },
    ])
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))

    await userEvent.selectOptions(screen.getByTestId('decision-sessions-district-filter'), 'Ba Dinh')

    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(1))
    expect(screen.getByText('run-2')).toBeInTheDocument()
  })

  it('shows a loading indicator before the sessions query resolves', async () => {
    let resolveSessions: (v: unknown) => void = () => {}
    vi.mocked(api.getDecisionSessions).mockImplementation(() => new Promise(resolve => { resolveSessions = resolve }))

    renderPanel()
    expect(screen.getByTestId('decision-sessions-loading')).toBeInTheDocument()

    resolveSessions([])
    await waitFor(() => expect(screen.queryByTestId('decision-sessions-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the sessions query fails', async () => {
    vi.mocked(api.getDecisionSessions).mockRejectedValue(new Error('network down'))

    renderPanel()
    await waitFor(() => expect(screen.getByTestId('decision-sessions-error')).toBeInTheDocument())
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    localStorage.setItem('civitas-language', 'vi')
    renderPanel()

    await waitFor(() => expect(screen.getByText('Phiên quyết định')).toBeInTheDocument())
    localStorage.removeItem('civitas-language')
  })

  it('expands and collapses the real outcome evidence list when its toggle is clicked', async () => {
    const evaluatedSession: DecisionSession = {
      ...observingSession,
      status: 'evaluated',
      observed_scores: { traffic_score: 60, environment_score: 70, citizen_score: 75, risk_score: 20, overall_score: 65 },
      outcome_status: 'improved',
      outcome_delta: { overall_score: 10 },
      success_rate: 80,
      outcome_evidence: [
        { source: 'CityScoreService', type: 'sensor_derived', metric: 'traffic_score', value: 60, confidence: 90, timestamp: '2026-07-21T09:30:00Z' },
        { source: 'CityScoreService', type: 'sensor_derived', metric: 'overall_score', value: 65, confidence: 90, timestamp: '2026-07-21T09:30:00Z' },
      ],
    }
    vi.mocked(api.getDecisionSessions).mockResolvedValue([evaluatedSession])

    renderPanel()
    await waitFor(() => expect(screen.getByTestId('session-evidence-toggle')).toBeInTheDocument())
    expect(screen.queryByTestId('session-evidence-list')).not.toBeInTheDocument()

    await userEvent.click(screen.getByTestId('session-evidence-toggle'))

    await waitFor(() => expect(screen.getByTestId('session-evidence-list')).toBeInTheDocument())
    const list = screen.getByTestId('session-evidence-list')
    expect(list).toHaveTextContent('CityScoreService')
    expect(list).toHaveTextContent('90%')
    expect(list).toHaveTextContent('60')
    expect(list).toHaveTextContent('65')

    await userEvent.click(screen.getByTestId('session-evidence-toggle'))
    expect(screen.queryByTestId('session-evidence-list')).not.toBeInTheDocument()
  })

  it('does not render the evidence toggle when outcome_evidence is null', async () => {
    renderPanel()
    await waitFor(() => expect(screen.getAllByTestId('decision-session-card')).toHaveLength(2))
    expect(screen.queryByTestId('session-evidence-toggle')).not.toBeInTheDocument()
  })
})
