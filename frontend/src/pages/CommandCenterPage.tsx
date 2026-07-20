import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Send, CheckCircle, XCircle, Bot, User, Wifi, WifiOff } from 'lucide-react'
import { api } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import HanoiMap from '../components/HanoiMap'
import AgentGraph from '../components/AgentGraph'
import SimulatorModal from '../components/SimulatorModal'
import EvidenceModal from '../components/EvidenceModal'
import type { AgentEvent, DecisionOut } from '../types'

// ─── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, unit, color }: { label: string; value: string | number; unit?: string; color: string }) {
  return (
    <div className={`bg-slate-900 border ${color} rounded-lg px-4 py-3 flex flex-col gap-0.5 min-w-[110px]`}>
      <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
      <span className="text-2xl font-bold text-slate-100 tabular-nums">{value}<span className="text-sm font-normal text-slate-400 ml-1">{unit}</span></span>
    </div>
  )
}

// ─── Agent Status Row ──────────────────────────────────────────────────────────
const PIPELINE_AGENTS = [
  'Traffic Agent', 'Environment Agent', 'Event Agent',
  'Citizen Agent', 'Knowledge Agent', 'Decision Agent', 'Explanation Agent',
]

function AgentMonitor({ events }: { events: AgentEvent[] }) {
  const statusMap = new Map<string, string>()
  let supervisorStatus = 'idle'

  for (const e of events) {
    if (e.type === 'pipeline_start') supervisorStatus = 'planning'
    else if (e.type === 'pipeline_done') supervisorStatus = 'done'
    else if (e.type === 'agent_update') statusMap.set(e.agent, e.status)
    else if (e.type === 'approval_needed') supervisorStatus = 'waiting'
    else if (e.type === 'approval_result') supervisorStatus = e.status === 'approved' ? 'done' : 'done'
  }

  const dot = (status: string) => {
    if (status === 'running') return 'bg-blue-500 animate-pulse'
    if (status === 'done') return 'bg-green-500'
    if (status === 'planning' || status === 'waiting') return 'bg-yellow-500 animate-pulse'
    return 'bg-slate-600'
  }

  const label = (status: string) => {
    if (status === 'running') return <span className="text-blue-400 text-xs">Running</span>
    if (status === 'done') return <span className="text-green-400 text-xs">Done</span>
    if (status === 'planning') return <span className="text-yellow-400 text-xs">Planning</span>
    if (status === 'waiting') return <span className="text-yellow-400 text-xs">Waiting</span>
    return <span className="text-slate-500 text-xs">Idle</span>
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between py-1 px-2 rounded bg-slate-900/60">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${dot(supervisorStatus)}`} />
          <span className="text-xs text-slate-300 font-medium">Supervisor</span>
        </div>
        {label(supervisorStatus)}
      </div>
      {PIPELINE_AGENTS.map(name => {
        const status = statusMap.get(name) ?? 'idle'
        return (
          <div key={name} className="flex items-center justify-between py-1 px-2 rounded bg-slate-900/40">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${dot(status)}`} />
              <span className="text-xs text-slate-400">{name.replace(' Agent', '')}</span>
            </div>
            {label(status)}
          </div>
        )
      })}
    </div>
  )
}

// ─── Agent Timeline ────────────────────────────────────────────────────────────
function AgentTimeline({ events }: { events: AgentEvent[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [events])

  if (events.length === 0) {
    return <div className="text-slate-600 text-xs text-center py-4">No events yet</div>
  }

  const icon = (e: AgentEvent) => {
    if (e.status === 'running') return '⟳'
    if (e.status === 'done') return '✓'
    if (e.status === 'waiting' || e.status === 'planning') return '◎'
    if (e.status === 'approved') return '✅'
    if (e.status === 'rejected') return '❌'
    return '•'
  }

  return (
    <div ref={ref} className="space-y-1 overflow-y-auto max-h-full pr-1 custom-scrollbar">
      {events.slice(-20).map((e, i) => (
        <div key={i} className="flex items-start gap-2 text-xs">
          <span className="text-slate-600 shrink-0 tabular-nums">{new Date(e.ts).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          <span className="text-slate-500 shrink-0">{icon(e)}</span>
          <span className="text-slate-300 font-medium shrink-0">{e.agent}</span>
          <span className="text-slate-500 truncate">{e.detail || e.status}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Decision Panel ────────────────────────────────────────────────────────────
function DecisionPanel({
  decision, pendingDecisionId, onApprove, onReject, onEvidenceClick
}: {
  decision: DecisionOut | null
  pendingDecisionId: number | null
  onApprove: () => void
  onReject: () => void
  onEvidenceClick: () => void
}) {
  if (!decision) return (
    <div className="flex items-center justify-center h-full text-slate-600 text-sm">
      Send a query to see AI decision
    </div>
  )

  return (
    <div className="space-y-3 text-sm overflow-y-auto custom-scrollbar h-full pr-1">
      {/* Confidence bar */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-400">Confidence</span>
          <span className={`font-mono font-bold ${decision.confidence >= 80 ? 'text-green-400' : decision.confidence >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
            {Math.round(decision.confidence)}%
          </span>
        </div>
        <div className="h-1.5 bg-slate-700 rounded-full">
          <div
            className={`h-1.5 rounded-full transition-all duration-1000 ${decision.confidence >= 80 ? 'bg-green-500' : decision.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${decision.confidence}%` }}
          />
        </div>
      </div>

      {/* Predictions */}
      {Object.keys(decision.prediction).length > 0 && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">Prediction</p>
          <div className="space-y-1">
            {Object.entries(decision.prediction).map(([k, v]) => (
              <div key={k} className="flex justify-between bg-slate-900/60 rounded px-2 py-1">
                <span className="text-slate-400 capitalize text-xs">{k.replace(/_/g, ' ')}</span>
                <span className="text-slate-200 text-xs font-medium">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {decision.recommendations.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">Recommendations</p>
          <ul className="space-y-1">
            {decision.recommendations.map((r, i) => (
              <li
                key={i}
                data-testid="recommendation-item"
                onClick={decision.evidence.length > 0 ? onEvidenceClick : undefined}
                className={`flex gap-2 text-xs text-slate-300 ${decision.evidence.length > 0 ? 'cursor-pointer hover:text-slate-100' : ''}`}
              >
                <span className="text-blue-400 shrink-0 mt-0.5">▸</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
          {decision.evidence.length > 0 && (
            <p className="text-[10px] text-slate-600 mt-1.5">Click a recommendation to view supporting evidence</p>
          )}
        </div>
      )}

      {/* Approval buttons */}
      {pendingDecisionId && (
        <div className="border border-yellow-500/30 rounded-lg p-3 bg-yellow-500/5">
          <p className="text-yellow-400 text-xs font-medium mb-2">⚠ Human approval required</p>
          <div className="flex gap-2">
            <button
              onClick={onApprove}
              className="flex-1 flex items-center justify-center gap-1.5 bg-green-600 hover:bg-green-500 text-white text-xs rounded-lg py-2 transition-colors"
            >
              <CheckCircle size={14} /> Approve
            </button>
            <button
              onClick={onReject}
              className="flex-1 flex items-center justify-center gap-1.5 bg-red-700 hover:bg-red-600 text-white text-xs rounded-lg py-2 transition-colors"
            >
              <XCircle size={14} /> Reject
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
type ChatMsg = { role: 'user' | 'ai'; text: string }
type ViewTab = 'graph' | 'monitor'


export default function CommandCenterPage() {
  const qc = useQueryClient()
  const [selectedDistrict, setSelectedDistrict] = useState<number>(1)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([])
  const [decision, setDecision] = useState<DecisionOut | null>(null)
  const [pendingDecisionId, setPendingDecisionId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [viewTab, setViewTab] = useState<ViewTab>('graph')
  const [simulatorOpen, setSimulatorOpen] = useState(false)
  const [simulatorRunning, setSimulatorRunning] = useState(false)
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [] } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })

  const selectedName = districts.find(d => d.id === selectedDistrict)?.name ?? `District ${selectedDistrict}`
  const selectedScore = scores.find(s => s.district_id === selectedDistrict)

  const cityHealth = scores.length
    ? Math.round(scores.reduce((a, s) => a + s.overall_score, 0) / scores.length)
    : 0

  const onEvent = useCallback((e: AgentEvent) => {
    setAgentEvents(prev => [...prev, e])
    if (e.type === 'pipeline_start') {
      setAgentEvents([e])
      setDecision(null)
      setPendingDecisionId(null)
    }
    if (e.type === 'approval_needed') {
      const match = e.detail.match(/Decision ID (\d+)/)
      if (match) setPendingDecisionId(Number(match[1]))
    }
  }, [])

  const { connected } = useWebSocket(onEvent)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendChat() {
    if (!query.trim() || loading) return
    const text = query.trim()
    setQuery('')
    setMessages(prev => [...prev, { role: 'user', text }])
    setLoading(true)
    try {
      const result = await api.chat(text, selectedDistrict)
      setDecision(result)
      setMessages(prev => [...prev, {
        role: 'ai',
        text: result.explanation[result.explanation.length - 1] ?? 'Analysis complete.',
      }])
      qc.invalidateQueries({ queryKey: ['scores'] })
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error calling AI pipeline. Check backend.' }])
    } finally {
      setLoading(false)
    }
  }

  async function runScenario(scenario: string) {
    setSimulatorRunning(true)
    setMessages(prev => [...prev, { role: 'user', text: `[Kịch bản] ${scenario} tại ${selectedName}` }])
    setLoading(true)
    try {
      const result = await api.simulate(scenario, selectedDistrict)
      setDecision(result)
      setMessages(prev => [...prev, {
        role: 'ai',
        text: result.explanation.at(-1) ?? 'Mô phỏng hoàn thành.',
      }])
      qc.invalidateQueries({ queryKey: ['scores'] })
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: 'Lỗi mô phỏng. Kiểm tra backend.' }])
    } finally {
      setLoading(false)
      setSimulatorRunning(false)
    }
  }

  async function handleApprove() {
    if (!pendingDecisionId) return
    await api.approveDecision(pendingDecisionId)
    setPendingDecisionId(null)
  }

  async function handleReject() {
    if (!pendingDecisionId) return
    await api.rejectDecision(pendingDecisionId)
    setPendingDecisionId(null)
  }

  return (
    <div data-testid="mission-control" className="flex flex-col h-screen bg-slate-950 overflow-hidden">
      {/* ── Header ── */}
      <header data-testid="app-header" className="flex items-center justify-between px-5 py-2.5 bg-slate-900 border-b border-slate-800 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-xs font-bold text-white">CO</div>
          <div>
            <p className="text-sm font-bold text-slate-100 leading-none">CityOS Mission Control</p>
            <p className="text-xs text-slate-500 leading-none mt-0.5">Hanoi · AI Operations Center</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div data-testid="connection-status" className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border ${connected ? 'border-green-500/30 text-green-400 bg-green-500/10' : 'border-red-500/30 text-red-400 bg-red-500/10'}`}>
            {connected ? <Wifi size={11} /> : <WifiOff size={11} />}
            {connected ? 'Live' : 'Disconnected'}
          </div>
          <div className="text-xs text-slate-500 font-mono">{new Date().toLocaleTimeString('vi-VN')}</div>
        </div>
      </header>

      {/* ── 3-Column Body ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── Left: Agent Panel ── */}
        <div className="w-64 shrink-0 flex flex-col border-r border-slate-800 bg-slate-900/50 overflow-hidden">
          <div className="flex border-b border-slate-800 shrink-0">
            {(['graph', 'monitor'] as ViewTab[]).map(t => (
              <button
                key={t}
                onClick={() => setViewTab(t)}
                className={`flex-1 py-2 text-xs font-medium capitalize transition-colors ${viewTab === t ? 'text-blue-400 bg-slate-900' : 'text-slate-500 hover:text-slate-300'}`}
              >
                {t === 'graph' ? 'Agent Graph' : 'Monitor'}
              </button>
            ))}
          </div>

          <div className="flex-1 p-2 overflow-hidden">
            {viewTab === 'graph' ? (
              <div className="h-full">
                <AgentGraph events={agentEvents} />
              </div>
            ) : (
              <AgentMonitor events={agentEvents} />
            )}
          </div>

          {/* Agent Timeline */}
          <div className="border-t border-slate-800 p-2 h-40 shrink-0">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5 px-1">Timeline</p>
            <AgentTimeline events={agentEvents} />
          </div>
        </div>

        {/* ── Center: Digital Twin Map ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* District info bar */}
          <div className="shrink-0 px-4 py-2 border-b border-slate-800 bg-slate-900/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Selected:</span>
              <span className="text-sm font-semibold text-blue-400">{selectedName}</span>
            </div>
            {selectedScore && (
              <div className="flex gap-4 text-xs">
                {[
                  { label: 'Overall', val: selectedScore.overall_score, cls: 'text-slate-200' },
                  { label: 'Traffic', val: selectedScore.traffic_score, cls: 'text-blue-400' },
                  { label: 'Env', val: selectedScore.environment_score, cls: 'text-teal-400' },
                  { label: 'Risk', val: selectedScore.risk_score, cls: 'text-orange-400' },
                ].map(({ label, val, cls }) => (
                  <span key={label} className={cls}>
                    <span className="text-slate-500">{label}: </span>
                    <span className="font-mono font-bold">{Math.round(val)}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Map */}
          <div className="flex-1 p-3 overflow-hidden">
            <HanoiMap
              scores={scores}
              selectedDistrictId={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
            />
          </div>

          {/* KPI bottom bar */}
          <div className="shrink-0 px-4 py-3 border-t border-slate-800 bg-slate-900/50 flex gap-3 overflow-x-auto">
            <KpiCard label="City Health" value={cityHealth} unit="/100" color={cityHealth >= 80 ? 'border-green-500/30' : cityHealth >= 60 ? 'border-yellow-500/30' : 'border-red-500/30'} />
            <KpiCard label="Districts" value={districts.length} unit="zones" color="border-slate-700" />
            {selectedScore && (
              <>
                <KpiCard label="Traffic" value={Math.round(selectedScore.traffic_score)} unit="/100" color="border-blue-500/30" />
                <KpiCard label="Air Quality" value={Math.round(selectedScore.environment_score)} unit="/100" color="border-teal-500/30" />
                <KpiCard label="Risk" value={Math.round(selectedScore.risk_score)} unit="/100" color={selectedScore.risk_score >= 60 ? 'border-red-500/30' : 'border-orange-500/30'} />
              </>
            )}
            {/* Simulator trigger */}
            <div className="ml-auto">
              <button
                data-testid="simulator-btn"
                onClick={() => setSimulatorOpen(true)}
                className="bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded-lg px-4 py-2 font-medium transition-colors h-full"
              >
                🎮 Mô phỏng
              </button>
            </div>
          </div>
        </div>

        {/* ── Right: AI Panel ── */}
        <div className="w-80 shrink-0 flex flex-col border-l border-slate-800 bg-slate-900/50 overflow-hidden">
          {/* Chat */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="shrink-0 px-4 py-2 border-b border-slate-800">
              <p className="text-xs font-semibold text-slate-300">AI Copilot</p>
              <p className="text-xs text-slate-600">Ask about {selectedName}</p>
            </div>

            <div data-testid="chat-messages" className="flex-1 overflow-y-auto px-3 py-3 space-y-2 custom-scrollbar">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Bot size={28} className="mx-auto text-slate-700 mb-2" />
                  <p className="text-xs text-slate-600">Ask about city conditions,<br />risk assessment, or run a simulation</p>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${m.role === 'user' ? 'bg-slate-700' : 'bg-blue-600'}`}>
                    {m.role === 'user' ? <User size={12} className="text-slate-300" /> : <Bot size={12} className="text-white" />}
                  </div>
                  <div className={`text-xs rounded-xl px-3 py-2 max-w-[85%] ${m.role === 'user' ? 'bg-blue-700 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700'}`}>
                    {m.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-2">
                  <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center">
                    <Bot size={12} className="text-white" />
                  </div>
                  <div className="bg-slate-800 border border-slate-700 rounded-xl rounded-tl-none px-3 py-2 flex gap-1">
                    {[0, 150, 300].map(d => (
                      <div key={d} className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="shrink-0 p-3 border-t border-slate-800">
              <div className="flex gap-2">
                <input
                  data-testid="chat-input"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendChat()}
                  placeholder="Ask AI about the city..."
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500"
                />
                <button
                  data-testid="chat-send"
                  onClick={sendChat}
                  disabled={loading || !query.trim()}
                  className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded-lg transition-colors"
                >
                  <Send size={14} className="text-white" />
                </button>
              </div>
            </div>
          </div>

          {/* Decision panel */}
          <div className="h-72 border-t border-slate-800 flex flex-col overflow-hidden shrink-0">
            <div className="shrink-0 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-300">Decision Report</p>
              {pendingDecisionId && (
                <span className="text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded-full animate-pulse">
                  Approval Needed
                </span>
              )}
            </div>
            <div className="flex-1 overflow-hidden p-3">
              <DecisionPanel
                decision={decision}
                pendingDecisionId={pendingDecisionId}
                onApprove={handleApprove}
                onReject={handleReject}
                onEvidenceClick={() => setEvidenceModalOpen(true)}
              />
            </div>
          </div>
        </div>
      </div>

      {simulatorOpen && (
        <SimulatorModal
          districtName={selectedName}
          onRun={runScenario}
          onClose={() => setSimulatorOpen(false)}
          events={agentEvents}
          running={simulatorRunning}
        />
      )}

      {evidenceModalOpen && decision && (
        <EvidenceModal
          evidence={decision.evidence}
          onClose={() => setEvidenceModalOpen(false)}
        />
      )}
    </div>
  )
}
