import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import SimulationPanel from '../../components/SimulationPanel'
import { api } from '../../services/api'

vi.mock('../../services/api')

beforeEach(() => {
  vi.mocked(api.getScenarios).mockResolvedValue([
    { name: 'heavy_rain', label: 'Mưa lớn' },
    { name: 'heatwave', label: 'Nắng nóng gay gắt' },
  ])
  vi.mocked(api.getSimulationStatus).mockResolvedValue({
    running: false, scenario: 'normal', scenario_label: 'Bình thường', interval_s: 30, auto_goal: true, tick: 0,
    values: { rain: 0, aqi: 60, temperature: 28, humidity: 65, wind_speed: 8 }, last_auto_goal: null,
  })
})

describe('SimulationPanel', () => {
  it('highlights rain as the trigger metric when the running scenario is heavy_rain', async () => {
    vi.mocked(api.getSimulationStatus).mockResolvedValue({
      running: true, scenario: 'heavy_rain', scenario_label: 'Mưa lớn', interval_s: 30, auto_goal: true, tick: 5,
      values: { rain: 42, aqi: 80, temperature: 27, humidity: 80, wind_speed: 10 }, last_auto_goal: null,
    })

    renderWithQueryClient(<SimulationPanel />)

    await waitFor(() => expect(screen.getByTestId('sim-values')).toBeInTheDocument())
    const rainSpan = screen.getByText('Mưa 42mm')
    const aqiSpan = screen.getByText('AQI 80')
    expect(rainSpan.className).toContain('font-semibold')
    expect(aqiSpan.className).not.toContain('font-semibold')
  })

  it('highlights temperature as the trigger metric when the running scenario is heatwave', async () => {
    vi.mocked(api.getSimulationStatus).mockResolvedValue({
      running: true, scenario: 'heatwave', scenario_label: 'Nắng nóng gay gắt', interval_s: 30, auto_goal: true, tick: 5,
      values: { rain: 0, aqi: 130, temperature: 39, humidity: 40, wind_speed: 5 }, last_auto_goal: null,
    })

    renderWithQueryClient(<SimulationPanel />)

    await waitFor(() => expect(screen.getByTestId('sim-values')).toBeInTheDocument())
    const tempSpan = screen.getByText('39°C')
    const rainSpan = screen.getByText('Mưa 0mm')
    expect(tempSpan.className).toContain('font-semibold')
    expect(rainSpan.className).not.toContain('font-semibold')
  })

  it('highlights no metric for major_event, since its trigger is not a weather reading', async () => {
    vi.mocked(api.getSimulationStatus).mockResolvedValue({
      running: true, scenario: 'major_event', scenario_label: 'Sự kiện đông người', interval_s: 30, auto_goal: true, tick: 5,
      values: { rain: 1, aqi: 120, temperature: 30, humidity: 60, wind_speed: 8 }, last_auto_goal: null,
    })

    renderWithQueryClient(<SimulationPanel />)

    await waitFor(() => expect(screen.getByTestId('sim-values')).toBeInTheDocument())
    expect(screen.getByText('Mưa 1mm').className).not.toContain('font-semibold')
    expect(screen.getByText('AQI 120').className).not.toContain('font-semibold')
    expect(screen.getByText('30°C').className).not.toContain('font-semibold')
  })

  it('shows the auto-goal cooldown remaining while one is active', async () => {
    vi.mocked(api.getSimulationStatus).mockResolvedValue({
      running: true, scenario: 'heavy_rain', scenario_label: 'Mưa lớn', interval_s: 30, auto_goal: true, tick: 5,
      values: { rain: 42, aqi: 80, temperature: 27, humidity: 80, wind_speed: 10 },
      last_auto_goal: 'run-123', auto_goal_cooldown_remaining_s: 180,
    })

    renderWithQueryClient(<SimulationPanel />)

    await waitFor(() => expect(screen.getByTestId('sim-cooldown')).toBeInTheDocument())
    expect(screen.getByTestId('sim-cooldown')).toHaveTextContent('180')
  })

  it('does not show a cooldown indicator when no cooldown is active', async () => {
    vi.mocked(api.getSimulationStatus).mockResolvedValue({
      running: true, scenario: 'heavy_rain', scenario_label: 'Mưa lớn', interval_s: 30, auto_goal: true, tick: 5,
      values: { rain: 42, aqi: 80, temperature: 27, humidity: 80, wind_speed: 10 },
      last_auto_goal: null, auto_goal_cooldown_remaining_s: 0,
    })

    renderWithQueryClient(<SimulationPanel />)

    await waitFor(() => expect(screen.getByTestId('sim-values')).toBeInTheDocument())
    expect(screen.queryByTestId('sim-cooldown')).not.toBeInTheDocument()
  })

  it('starts the simulation targeting the district passed in via props', async () => {
    vi.mocked(api.startSimulation).mockResolvedValue({
      running: true, scenario: 'heavy_rain', scenario_label: 'Mưa lớn', interval_s: 30, auto_goal: true, tick: 1,
      district_id: 3, values: { rain: 0, aqi: 60, temperature: 28, humidity: 65, wind_speed: 8 }, last_auto_goal: null,
    })

    const user = userEvent.setup()
    renderWithQueryClient(<SimulationPanel districtId={3} />)

    await user.click(await screen.findByTestId('sim-start-btn'))

    await waitFor(() => expect(api.startSimulation).toHaveBeenCalledWith('heavy_rain', 30, true, 3))
  })

  it('shows the real per-source counts after a crawl, including a zero-count source', async () => {
    vi.mocked(api.runCrawl).mockResolvedValue({
      weather: { ok: true, count: 12 },
      aqi: { ok: true, count: 0 },
      news: { ok: false, error: 'network down' },
    })

    const user = userEvent.setup()
    renderWithQueryClient(<SimulationPanel />)

    await user.click(screen.getByTestId('sim-crawl-btn'))

    const results = await screen.findByTestId('sim-crawl-results')
    expect(results).toHaveTextContent('12 mục')
    // A source that ran but wrote nothing (e.g. AQI with no API key
    // configured) must show its real zero count, not a generic "OK".
    expect(results).toHaveTextContent('0 mục')
    expect(results).toHaveTextContent('lỗi')
  })
})
