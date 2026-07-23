import { describe, it, expect, vi, beforeEach } from 'vitest'

// hoisted: runs before any imports, so the mock instance is available when api.ts loads
const mockHttp = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))

vi.mock('axios', () => ({
  default: { create: vi.fn(() => mockHttp) },
}))

import { api, createWebSocket } from '../../services/api'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('api.getDistricts', () => {
  it('GETs /api/districts and returns data array', async () => {
    const districts = [{ id: 1, city_id: 'hanoi', name: 'Hoàn Kiếm' }]
    mockHttp.get.mockResolvedValueOnce({ data: districts })
    const result = await api.getDistricts()
    expect(mockHttp.get).toHaveBeenCalledWith('/api/districts')
    expect(result).toEqual(districts)
  })
})

describe('api.getScores', () => {
  it('GETs /api/scores and returns array', async () => {
    const scores = [{ id: 1, district_id: 1, overall_score: 75 }]
    mockHttp.get.mockResolvedValueOnce({ data: scores })
    const result = await api.getScores()
    expect(result).toEqual(scores)
  })
})

describe('api.chat', () => {
  it('POSTs query and district_id to /api/chat', async () => {
    const decision = { prediction: {}, impact: {}, recommendations: [], confidence: 80, explanation: [] }
    mockHttp.post.mockResolvedValueOnce({ data: decision })
    const result = await api.chat('What is the AQI?', 3)
    expect(mockHttp.post).toHaveBeenCalledWith('/api/chat', { query: 'What is the AQI?', district_id: 3 })
    expect(result).toEqual(decision)
  })
})

describe('api.simulate', () => {
  it('POSTs scenario and district_id to /api/simulate', async () => {
    const decision = { prediction: { flood_risk: 'high' }, impact: {}, recommendations: [], confidence: 65, explanation: [] }
    mockHttp.post.mockResolvedValueOnce({ data: decision })
    const result = await api.simulate('heavy_rain', 1)
    expect(mockHttp.post).toHaveBeenCalledWith('/api/simulate', { scenario: 'heavy_rain', district_id: 1 })
    expect(result.prediction.flood_risk).toBe('high')
  })
})

describe('api.approveDecision', () => {
  it('POSTs to /api/decisions/:id/approve', async () => {
    mockHttp.post.mockResolvedValueOnce({ data: { id: 5, approved: true } })
    await api.approveDecision(5)
    expect(mockHttp.post).toHaveBeenCalledWith('/api/decisions/5/approve')
  })
})

describe('api.rejectDecision', () => {
  it('POSTs to /api/decisions/:id/reject', async () => {
    mockHttp.post.mockResolvedValueOnce({ data: { id: 5, approved: false } })
    await api.rejectDecision(5)
    expect(mockHttp.post).toHaveBeenCalledWith('/api/decisions/5/reject')
  })
})

describe('api.getKnowledgeSummary', () => {
  it('sends a higher default limit even without a search query, so the default view is not capped at 5 samples', async () => {
    mockHttp.get.mockResolvedValueOnce({ data: { configured: true, entities: 1, relations: 1, sample: [] } })
    await api.getKnowledgeSummary()
    expect(mockHttp.get).toHaveBeenCalledWith('/api/knowledge/summary', { params: { limit: 15 } })
  })

  it('includes the search query alongside the limit when provided', async () => {
    mockHttp.get.mockResolvedValueOnce({ data: { configured: true, entities: 1, relations: 1, sample: [] } })
    await api.getKnowledgeSummary('Cau Giay')
    expect(mockHttp.get).toHaveBeenCalledWith('/api/knowledge/summary', { params: { limit: 15, q: 'Cau Giay' } })
  })

  it('allows overriding the default limit, e.g. for an entity detail drill-down', async () => {
    mockHttp.get.mockResolvedValueOnce({ data: { configured: true, entities: 1, relations: 1, sample: [] } })
    await api.getKnowledgeSummary('Hoan Kiem', 30)
    expect(mockHttp.get).toHaveBeenCalledWith('/api/knowledge/summary', { params: { limit: 30, q: 'Hoan Kiem' } })
  })
})

describe('api.getScoreHistory', () => {
  it('GETs /api/scores/history/:id with a limit param', async () => {
    const points = [{ time: '09:00', traffic_score: 80, environment_score: 70, citizen_score: 65, risk_score: 20 }]
    mockHttp.get.mockResolvedValueOnce({ data: points })
    const result = await api.getScoreHistory(3, 12)
    expect(mockHttp.get).toHaveBeenCalledWith('/api/scores/history/3', { params: { limit: 12 } })
    expect(result).toEqual(points)
  })

  it('defaults the limit to 12 when not provided', async () => {
    mockHttp.get.mockResolvedValueOnce({ data: [] })
    await api.getScoreHistory(1)
    expect(mockHttp.get).toHaveBeenCalledWith('/api/scores/history/1', { params: { limit: 12 } })
  })
})

describe('createWebSocket', () => {
  it('creates ws:// URL when page is http', () => {
    Object.defineProperty(window, 'location', {
      value: { protocol: 'http:', host: 'localhost:3000' },
      writable: true,
    })
    const mockWs = {}
    const WS = vi.fn(() => mockWs)
    global.WebSocket = WS as unknown as typeof WebSocket
    const ws = createWebSocket()
    expect(WS).toHaveBeenCalledWith('ws://localhost:3000/ws')
    expect(ws).toBe(mockWs)
  })

  it('creates wss:// URL when page is https', () => {
    Object.defineProperty(window, 'location', {
      value: { protocol: 'https:', host: 'civitas.example.com' },
      writable: true,
    })
    const WS = vi.fn(() => ({}))
    global.WebSocket = WS as unknown as typeof WebSocket
    createWebSocket()
    expect(WS).toHaveBeenCalledWith('wss://civitas.example.com/ws')
  })
})
