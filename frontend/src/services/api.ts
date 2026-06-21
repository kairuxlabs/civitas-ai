import axios from 'axios'
import type { District, CityScore, DecisionOut, AgentDecisionOut } from '../types'

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
}
