import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { renderWithQueryClient } from '../test-utils'
import OverviewPage from '../../pages/stitch/OverviewPage'
import { api } from '../../services/api'
import { LanguageProvider } from '../../i18n/LanguageContext'

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
    renderWithQueryClient(
      <LanguageProvider>
        <MemoryRouter>
          <OverviewPage />
        </MemoryRouter>
      </LanguageProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('overview-page')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByTestId('overview-overall-score')).toHaveTextContent('74'))
  })

  it('shows a loading indicator before the scores query resolves', async () => {
    let resolveScores: (v: unknown) => void = () => {}
    vi.mocked(api.getScores).mockImplementation(() => new Promise(resolve => { resolveScores = resolve }))

    renderWithQueryClient(
      <LanguageProvider>
        <MemoryRouter>
          <OverviewPage />
        </MemoryRouter>
      </LanguageProvider>,
    )
    expect(screen.getByTestId('overview-loading')).toBeInTheDocument()

    resolveScores([])
    await waitFor(() => expect(screen.queryByTestId('overview-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the scores query fails', async () => {
    vi.mocked(api.getScores).mockRejectedValue(new Error('network down'))

    renderWithQueryClient(
      <LanguageProvider>
        <MemoryRouter>
          <OverviewPage />
        </MemoryRouter>
      </LanguageProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('overview-error')).toBeInTheDocument())
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    localStorage.setItem('civitas-language', 'vi')

    renderWithQueryClient(
      <LanguageProvider>
        <MemoryRouter>
          <OverviewPage />
        </MemoryRouter>
      </LanguageProvider>,
    )

    await waitFor(() => expect(screen.getByText('Bảng trạng thái thành phố')).toBeInTheDocument())
    localStorage.removeItem('civitas-language')
  })
})
