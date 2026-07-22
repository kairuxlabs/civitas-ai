import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import SimulatorPage from '../../pages/SimulatorPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

beforeEach(() => {
  vi.mocked(api.getDistricts).mockResolvedValue([
    { id: 1, city_id: 'hanoi', name: 'Hoan Kiem' },
  ])
})

describe('SimulatorPage', () => {
  it('runs a scenario and renders the decision result', async () => {
    vi.mocked(api.simulate).mockResolvedValue({
      prediction: {}, impact: {}, recommendations: ['Deploy pumps'],
      confidence: 80, explanation: ['Looks fine'], evidence: [],
    })
    renderWithQueryClient(<SimulatorPage />)

    await userEvent.click(screen.getByText('Heavy Rain'))
    await userEvent.click(screen.getByRole('button', { name: /Run Simulation/i }))

    await waitFor(() => expect(screen.getByText('Deploy pumps')).toBeInTheDocument())
    expect(screen.queryByTestId('simulator-error')).not.toBeInTheDocument()
  })

  it('shows an inline error message when the simulate call fails, instead of failing silently', async () => {
    vi.mocked(api.simulate).mockRejectedValue(new Error('network down'))
    renderWithQueryClient(<SimulatorPage />)

    await userEvent.click(screen.getByText('Heavy Rain'))
    await userEvent.click(screen.getByRole('button', { name: /Run Simulation/i }))

    await waitFor(() => expect(screen.getByTestId('simulator-error')).toBeInTheDocument())
    expect(screen.getByTestId('simulator-error')).toHaveTextContent(/simulation failed/i)
    // Loading state must be cleared even though the call failed
    expect(screen.queryByText('Running simulation...')).not.toBeInTheDocument()
  })
})
