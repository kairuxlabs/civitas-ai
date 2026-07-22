import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import CityIntelligencePage from '../../pages/stitch/CityIntelligencePage'
import { api } from '../../services/api'
import { LanguageProvider } from '../../i18n/LanguageContext'

vi.mock('../../services/api')

function renderPage() {
  return renderWithQueryClient(<LanguageProvider><CityIntelligencePage /></LanguageProvider>)
}

beforeEach(() => {
  vi.mocked(api.getDistricts).mockResolvedValue([
    { id: 1, city_id: 'hanoi', name: 'Hoan Kiem' },
    { id: 2, city_id: 'hanoi', name: 'Ba Dinh' },
  ])
  vi.mocked(api.getScores).mockResolvedValue([
    {
      id: 1, city_id: 'hanoi', district_id: 1, timestamp: '2026-07-21T09:00:00Z',
      traffic_score: 82, environment_score: 68, citizen_score: 74, risk_score: 20, overall_score: 76,
    },
    {
      id: 2, city_id: 'hanoi', district_id: 2, timestamp: '2026-07-21T09:00:00Z',
      traffic_score: 60, environment_score: 50, citizen_score: 65, risk_score: 40, overall_score: 55,
    },
  ])
  vi.mocked(api.getAQIHistory).mockResolvedValue([
    { time: '2026-07-21T08:00:00Z', aqi_index: 90, pm25: 45 },
  ])
})

describe('CityIntelligencePage', () => {
  it('renders the overall score for the selected district from real scores data', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByTestId('city-intelligence-page')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByTestId('city-intelligence-overall-score')).toHaveTextContent('76'))
  })

  it('lists all districts as selectable', async () => {
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('city-intelligence-district-option')).toHaveLength(2))
  })

  it('renders an AQI trend chart from the fetched history once there is more than one data point', async () => {
    vi.mocked(api.getAQIHistory).mockResolvedValue([
      { time: '2026-07-21T06:00:00Z', aqi_index: 70, pm25: 30 },
      { time: '2026-07-21T07:00:00Z', aqi_index: 85, pm25: 40 },
      { time: '2026-07-21T08:00:00Z', aqi_index: 90, pm25: 45 },
    ])
    renderPage()
    await waitFor(() => expect(screen.getByTestId('city-intelligence-aqi-trend')).toBeInTheDocument())
  })

  it('does not render the AQI trend chart with fewer than two data points', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByTestId('city-intelligence-overall-score')).toBeInTheDocument())
    expect(screen.queryByTestId('city-intelligence-aqi-trend')).not.toBeInTheDocument()
  })

  it('shows a loading indicator before the scores query resolves', async () => {
    let resolveScores: (v: unknown) => void = () => {}
    vi.mocked(api.getScores).mockImplementation(() => new Promise(resolve => { resolveScores = resolve }))

    renderPage()
    expect(screen.getByTestId('city-intelligence-loading')).toBeInTheDocument()

    resolveScores([])
    await waitFor(() => expect(screen.queryByTestId('city-intelligence-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the scores query fails', async () => {
    vi.mocked(api.getScores).mockRejectedValue(new Error('network down'))

    renderPage()
    await waitFor(() => expect(screen.getByTestId('city-intelligence-error')).toBeInTheDocument())
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    localStorage.setItem('civitas-language', 'vi')
    renderPage()

    await waitFor(() => expect(screen.getByText('Thông tin thành phố')).toBeInTheDocument())
    localStorage.removeItem('civitas-language')
  })
})
