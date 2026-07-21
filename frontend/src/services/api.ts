import axios from 'axios'
import type {
  District, CityScore, DecisionOut, AgentDecisionOut, AQIPoint,
  RuntimeRun, RuntimeRunSummary, RuntimeMonitor,
  SimulationStatus, ScenarioInfo, CrawlResults,
  DecisionSession, DecisionSessionAnalytics, SystemStatus, KnowledgeSummary,
} from '../types'

const stripBOM = (s: string) => s.replace(/^﻿/, '').trim()
const baseURL = stripBOM(import.meta.env.VITE_API_BASE_URL || '')
const http = axios.create({ baseURL })

export const api = {
  getDistricts: () => http.get<District[]>('/api/districts').then(r => r.data),
  getScores: () => http.get<CityScore[]>('/api/scores').then(r => r.data),
  getHealth: () => http.get<{ status: string }>('/health').then(r => r.data),
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

  // CityOS v2 autonomous runtime
  submitGoal: (goal: string, districtId = 1) =>
    http.post<RuntimeRun>('/api/v2/goal', { goal, district_id: districtId }).then(r => r.data),
  getRuns: () => http.get<{ runs: RuntimeRunSummary[] }>('/api/v2/runs').then(r => r.data.runs),
  getRun: (runId: string) => http.get<RuntimeRun>(`/api/v2/runs/${runId}`).then(r => r.data),
  resolveRun: (runId: string, approved: boolean) =>
    http.post<RuntimeRun>(`/api/v2/runs/${runId}/approval`, { approved }).then(r => r.data),
  getRuntimeMonitor: () => http.get<RuntimeMonitor>('/api/v2/monitor').then(r => r.data),

  // Digital Twin simulation + crawling
  startSimulation: (scenario: string, intervalS = 30, autoGoal = true) =>
    http.post<SimulationStatus>('/api/v2/simulation/start', {
      scenario, interval_s: intervalS, auto_goal: autoGoal,
    }).then(r => r.data),
  stopSimulation: () => http.post<SimulationStatus>('/api/v2/simulation/stop').then(r => r.data),
  getSimulationStatus: () => http.get<SimulationStatus>('/api/v2/simulation/status').then(r => r.data),
  getScenarios: () =>
    http.get<{ scenarios: ScenarioInfo[] }>('/api/v2/simulation/scenarios').then(r => r.data.scenarios),
  runCrawl: (sources?: string[]) =>
    http.post<{ results: CrawlResults }>('/api/v2/crawl', { sources }).then(r => r.data.results),

  // Decision Session lifecycle
  getDecisionSessions: (status?: string) =>
    http.get<DecisionSession[]>('/api/decision-sessions', { params: status ? { status } : undefined })
      .then(r => r.data),
  getDecisionSession: (id: number) =>
    http.get<DecisionSession>(`/api/decision-sessions/${id}`).then(r => r.data),
  observeDecisionSession: (id: number) =>
    http.post<DecisionSession>(`/api/decision-sessions/${id}/observe`).then(r => r.data),
  getDecisionSessionAnalytics: () =>
    http.get<DecisionSessionAnalytics>('/api/decision-sessions/analytics').then(r => r.data),

  getSystemStatus: () => http.get<SystemStatus>('/api/system/status').then(r => r.data),
  getKnowledgeSummary: () => http.get<KnowledgeSummary>('/api/knowledge/summary').then(r => r.data),
}

export function createWebSocket(): WebSocket {
  const wsURL = stripBOM(import.meta.env.VITE_WS_URL || '')
  if (wsURL) {
    return new WebSocket(wsURL)
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/ws`)
}
