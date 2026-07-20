import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor, act } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import type { AgentEvent } from '../../types'

const mockHttp = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))

vi.mock('axios', () => ({
  default: { create: vi.fn(() => mockHttp) },
}))

let capturedOnEvent: ((e: AgentEvent) => void) | null = null

vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: (onEvent: (e: AgentEvent) => void) => {
    capturedOnEvent = onEvent
    return { connected: true }
  },
}))

import CommandCenterPage from '../../pages/CommandCenterPage'

const MOCK_DISTRICTS = [
  { id: 1, city_id: 'hanoi', name: 'Hoàn Kiếm' },
  { id: 2, city_id: 'hanoi', name: 'Ba Đình' },
]

const MOCK_SCORES = [
  { id: 1, city_id: 'hanoi', district_id: 1, timestamp: '2026-07-21T00:00:00Z', traffic_score: 70, environment_score: 65, citizen_score: 70, risk_score: 20, overall_score: 72 },
]

function mockDistrictsAndScores() {
  mockHttp.get.mockImplementation((url: string) => {
    if (url === '/api/districts') return Promise.resolve({ data: MOCK_DISTRICTS })
    if (url === '/api/scores') return Promise.resolve({ data: MOCK_SCORES })
    return Promise.reject(new Error(`unexpected GET ${url}`))
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  capturedOnEvent = null
})

describe('CommandCenterPage', () => {
  it('renders district selector data and KPI cards from mocked queries', async () => {
    mockDistrictsAndScores()
    renderWithQueryClient(<CommandCenterPage />)

    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())
    expect(screen.getByText('City Health')).toBeTruthy()
  })

  it('sends a chat message and displays the AI response', async () => {
    mockDistrictsAndScores()
    mockHttp.post.mockResolvedValueOnce({
      data: {
        prediction: { flood_risk: 'low' }, impact: {}, recommendations: ['Theo dõi thời tiết'],
        confidence: 80, explanation: ['Tình hình ổn định.'], evidence: [],
      },
    })
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.change(screen.getByTestId('chat-input'), { target: { value: 'Tình hình?' } })
    fireEvent.click(screen.getByTestId('chat-send'))

    await waitFor(() => expect(screen.getByText('Tình hình ổn định.')).toBeTruthy())
    expect(mockHttp.post).toHaveBeenCalledWith('/api/chat', { query: 'Tình hình?', district_id: 1 })
  })

  it('shows an error bubble when the chat call fails', async () => {
    mockDistrictsAndScores()
    mockHttp.post.mockRejectedValueOnce(new Error('network error'))
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.change(screen.getByTestId('chat-input'), { target: { value: 'Status?' } })
    fireEvent.click(screen.getByTestId('chat-send'))

    await waitFor(() => expect(screen.getByText('Error calling AI pipeline. Check backend.')).toBeTruthy())
  })

  it('approves a pending decision and clears the approval banner', async () => {
    mockDistrictsAndScores()
    mockHttp.post.mockImplementation((url: string) => {
      if (url === '/api/chat') {
        return Promise.resolve({
          data: { prediction: { flood_risk: 'high' }, impact: {}, recommendations: [], confidence: 40, explanation: ['...'], evidence: [] },
        })
      }
      if (url === '/api/decisions/7/approve') return Promise.resolve({ data: { id: 7, approved: true } })
      return Promise.reject(new Error(`unexpected POST ${url}`))
    })
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.change(screen.getByTestId('chat-input'), { target: { value: 'Status?' } })
    fireEvent.click(screen.getByTestId('chat-send'))
    await waitFor(() => expect(mockHttp.post).toHaveBeenCalledWith('/api/chat', expect.anything()))

    act(() => {
      capturedOnEvent?.({
        type: 'approval_needed', agent: 'Supervisor', status: 'waiting',
        detail: 'Decision ID 7 requires human approval', ts: '2026-07-21T00:00:00Z',
      })
    })
    await waitFor(() => expect(screen.getByText('Approval Needed')).toBeTruthy())

    fireEvent.click(screen.getByRole('button', { name: /Approve/i }))
    await waitFor(() => expect(mockHttp.post).toHaveBeenCalledWith('/api/decisions/7/approve'))
    await waitFor(() => expect(screen.queryByText('Approval Needed')).toBeNull())
  })

  it('opens the evidence modal when a recommendation is clicked', async () => {
    mockDistrictsAndScores()
    mockHttp.post.mockResolvedValueOnce({
      data: {
        prediction: {}, impact: {}, recommendations: ['Kích hoạt bơm thoát nước'],
        confidence: 70, explanation: ['...'],
        evidence: [
          { id: 'ev-1', agent: 'traffic', source: 'Open-Meteo', type: 'sensor', content: 'Rain 40mm/h', confidence: 0.9, time: '2026-07-21T00:00:00Z' },
        ],
      },
    })
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.change(screen.getByTestId('chat-input'), { target: { value: 'Status?' } })
    fireEvent.click(screen.getByTestId('chat-send'))
    await waitFor(() => expect(screen.getByTestId('recommendation-item')).toBeTruthy())

    fireEvent.click(screen.getByTestId('recommendation-item'))
    expect(screen.getByTestId('evidence-modal')).toBeTruthy()
    expect(screen.getByText('Rain 40mm/h')).toBeTruthy()
  })

  it('runs a sequential baseline-then-scenario flow from the simulator', async () => {
    mockDistrictsAndScores()
    const callOrder: string[] = []
    mockHttp.post.mockImplementation((url: string) => {
      callOrder.push(url)
      if (url === '/api/chat') {
        return Promise.resolve({
          data: { prediction: { flood_risk: 'low' }, impact: {}, recommendations: [], confidence: 75, explanation: ['...'], evidence: [] },
        })
      }
      if (url === '/api/simulate') {
        return Promise.resolve({
          data: { prediction: { flood_risk: 'high' }, impact: {}, recommendations: ['Sơ tán vùng thấp'], confidence: 55, explanation: ['...'], evidence: [] },
        })
      }
      return Promise.reject(new Error(`unexpected POST ${url}`))
    })
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.click(screen.getByTestId('simulator-btn'))
    fireEvent.click(screen.getByTestId('scenario-heavy_rain'))
    fireEvent.click(screen.getByTestId('simulator-run-btn'))

    await waitFor(() => expect(callOrder).toEqual(['/api/chat', '/api/simulate']))
    await waitFor(() => expect(screen.getByText('✓ So sánh Before/After')).toBeTruthy())
  })

  it('updates the Agent Monitor tab when a WebSocket agent_update event arrives', async () => {
    mockDistrictsAndScores()
    renderWithQueryClient(<CommandCenterPage />)
    await waitFor(() => expect(screen.getByText('Hoàn Kiếm')).toBeTruthy())

    fireEvent.click(screen.getByRole('button', { name: 'Monitor' }))
    act(() => {
      capturedOnEvent?.({ type: 'agent_update', agent: 'Traffic Agent', status: 'running', detail: '', ts: '2026-07-21T00:00:00Z' })
    })

    expect(screen.getByText('Running')).toBeTruthy()
  })
})
