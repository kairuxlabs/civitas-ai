import axios from 'axios'
import type { District, CityScore, DecisionOut, AgentDecisionOut, AQIPoint } from '../types'

const http = axios.create({ baseURL: '' })

export const api = {
  getDistricts: () => http.get<District[]>('/api/districts').then(r => r.data),
  getScores: () => http.get<CityScore[]>('/api/scores').then(r => r.data),
  getDistrictScore: (id: number) => http.get<CityScore>(`/api/scores/${id}`).then(r => r.data),
  chat: (query: string, districtId: number) =>
    http.post<DecisionOut>('/api/chat', { query, district_id: districtId }).then(r => r.data),
  simulate: (scenario: string, districtId: number) =>
    http.post<DecisionOut>('/api/simulate', { scenario, district_id: districtId }).then(r => r.data),
  getTimeline: (limit = 20) => http.get<AgentDecisionOut[]>(`/api/timeline?limit=${limit}`).then(r => r.data),
  getAQIHistory: (districtId: number, limit = 24) =>
    http.get<AQIPoint[]>(`/api/aqi/history/${districtId}?limit=${limit}`).then(r => r.data),
  approveDecision: (id: number) => http.post(`/api/decisions/${id}/approve`).then(r => r.data),
  rejectDecision: (id: number) => http.post(`/api/decisions/${id}/reject`).then(r => r.data),
}

export function createWebSocket(): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/ws`)
}
