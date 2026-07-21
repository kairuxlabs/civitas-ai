import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import ReportsPage from '../../pages/stitch/ReportsPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

const pendingReport = {
  id: 1, city_id: 'hanoi', district_id: 1, query: 'Prepare for heavy rain',
  prediction: {}, impact: {}, recommendations: [], confidence: 62,
  explanation: [], evidence: [], requires_approval: true, approved: null,
  created_at: '2026-07-21T09:00:00Z',
}

const completedReport = {
  ...pendingReport, id: 2, query: 'Air pollution response', approved: true, confidence: 88,
}

beforeEach(() => {
  vi.mocked(api.getTimeline).mockResolvedValue([pendingReport, completedReport])
  vi.mocked(api.approveDecision).mockResolvedValue({ id: 1, approved: true })
  vi.mocked(api.rejectDecision).mockResolvedValue({ id: 1, approved: false })
})

describe('ReportsPage', () => {
  it('renders one row per decision report from the real timeline', async () => {
    renderWithQueryClient(<ReportsPage />)
    await waitFor(() => expect(screen.getAllByTestId('report-row')).toHaveLength(2))
  })

  it('shows approve/reject actions only for reports still pending', async () => {
    renderWithQueryClient(<ReportsPage />)
    await waitFor(() => expect(screen.getAllByTestId('report-row')).toHaveLength(2))
    expect(screen.getAllByTestId('report-approve-button')).toHaveLength(1)
    expect(screen.getAllByTestId('report-reject-button')).toHaveLength(1)
  })

  it('approves a pending report and refetches the timeline', async () => {
    renderWithQueryClient(<ReportsPage />)
    await waitFor(() => expect(screen.getAllByTestId('report-approve-button')).toHaveLength(1))

    await userEvent.click(screen.getByTestId('report-approve-button'))

    await waitFor(() => expect(api.approveDecision).toHaveBeenCalledWith(1))
  })
})
