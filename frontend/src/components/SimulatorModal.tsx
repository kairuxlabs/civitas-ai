import { useState } from 'react'
import { X, Play, ChevronRight } from 'lucide-react'
import type { AgentEvent } from '../types'

interface Scenario {
  key: string
  label: string
  emoji: string
  desc: string
  tags: string[]
  color: string
  borderColor: string
}

const SCENARIOS: Scenario[] = [
  {
    key: 'heavy_rain',
    label: 'Lũ Lụt Nặng',
    emoji: '🌧',
    desc: 'Mưa 80mm/h tại toàn quận — nguy cơ ngập lụt, ách tắc giao thông trầm trọng',
    tags: ['flood_risk: HIGH', 'rain: ×10', 'AQI +20'],
    color: 'from-blue-900/60 to-slate-900',
    borderColor: 'border-blue-500',
  },
  {
    key: 'air_pollution',
    label: 'Ô Nhiễm Không Khí',
    emoji: '🌫',
    desc: 'AQI vượt 200+ mức nguy hiểm — cần đóng cửa trường học, giới hạn xe cộ',
    tags: ['AQI: HAZARDOUS', 'PM2.5 +80', 'alert: RED'],
    color: 'from-yellow-900/60 to-slate-900',
    borderColor: 'border-yellow-500',
  },
  {
    key: 'major_event',
    label: 'Sự Kiện Lớn',
    emoji: '🎉',
    desc: '50.000+ người tập trung — tắc nghẽn giao thông, an ninh, y tế cần phối hợp',
    tags: ['crowd: MASSIVE', 'traffic: BLOCKED', 'AQI +30'],
    color: 'from-purple-900/60 to-slate-900',
    borderColor: 'border-purple-500',
  },
  {
    key: 'heatwave',
    label: 'Sóng Nhiệt',
    emoji: '🔥',
    desc: 'Nhiệt độ 42°C kéo dài 3 ngày — cảnh báo sức khỏe, tăng tải điện lưới',
    tags: ['temp: 42°C', 'health: CRITICAL', 'AQI +50'],
    color: 'from-red-900/60 to-slate-900',
    borderColor: 'border-red-500',
  },
]

interface Props {
  districtName: string
  onRun: (scenarioKey: string) => void
  onClose: () => void
  events: AgentEvent[]
  running: boolean
}

export default function SimulatorModal({ districtName, onRun, onClose, events, running }: Props) {
  const [selected, setSelected] = useState<string | null>(null)
  const [launched, setLaunched] = useState(false)

  const pipelineEvents = events.filter(e =>
    e.type === 'agent_update' || e.type === 'pipeline_start' || e.type === 'pipeline_done'
  )

  const pipelineDone = events.some(e => e.type === 'pipeline_done')

  const handleRun = () => {
    if (!selected) return
    setLaunched(true)
    onRun(selected)
  }

  const PIPELINE_STEPS = [
    'Traffic Agent', 'Environment Agent', 'Event Agent',
    'Citizen Agent', 'Knowledge Agent', 'Decision Agent', 'Explanation Agent',
  ]

  function stepStatus(name: string): 'idle' | 'running' | 'done' {
    const match = events.filter(e => e.type === 'agent_update' && e.agent === name)
    if (match.some(e => e.status === 'done')) return 'done'
    if (match.some(e => e.status === 'running')) return 'running'
    return 'idle'
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950">
          <div>
            <p className="text-sm font-bold text-slate-100">What-If Simulator</p>
            <p className="text-xs text-slate-500 mt-0.5">Quận: <span className="text-blue-400">{districtName}</span></p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors p-1">
            <X size={18} />
          </button>
        </div>

        <div className="p-6">
          {!launched ? (
            <>
              {/* Scenario grid */}
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Chọn kịch bản</p>
              <div className="grid grid-cols-2 gap-3">
                {SCENARIOS.map(s => (
                  <button
                    key={s.key}
                    onClick={() => setSelected(s.key)}
                    className={`rounded-xl border p-4 text-left transition-all bg-gradient-to-br ${s.color} ${
                      selected === s.key
                        ? `${s.borderColor} shadow-lg shadow-black/40 scale-[1.02]`
                        : 'border-slate-700 hover:border-slate-500'
                    }`}
                  >
                    <div className="text-3xl mb-2">{s.emoji}</div>
                    <div className="text-sm font-semibold text-slate-100 mb-1">{s.label}</div>
                    <div className="text-xs text-slate-400 leading-relaxed mb-2">{s.desc}</div>
                    <div className="flex flex-wrap gap-1">
                      {s.tags.map(tag => (
                        <span key={tag} className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 rounded-full px-2 py-0.5">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </button>
                ))}
              </div>

              <button
                onClick={handleRun}
                disabled={!selected}
                className="mt-4 w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors text-sm"
              >
                <Play size={16} />
                Chạy mô phỏng
                <ChevronRight size={14} />
              </button>
            </>
          ) : (
            <>
              {/* Live pipeline progress */}
              <div className="space-y-2 mb-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Pipeline đang chạy</p>
                {PIPELINE_STEPS.map((step, i) => {
                  const status = stepStatus(step)
                  const shortName = step.replace(' Agent', '')
                  return (
                    <div key={step} className="flex items-center gap-3">
                      <div className="w-6 text-right text-xs text-slate-600 font-mono shrink-0">{i + 1}</div>
                      <div className={`flex-1 flex items-center gap-2.5 rounded-lg px-3 py-2 border transition-all ${
                        status === 'running' ? 'bg-blue-950/60 border-blue-500/50' :
                        status === 'done' ? 'bg-green-950/40 border-green-500/30' :
                        'bg-slate-900 border-slate-800'
                      }`}>
                        <div className={`w-2 h-2 rounded-full shrink-0 ${
                          status === 'running' ? 'bg-blue-400 animate-pulse' :
                          status === 'done' ? 'bg-green-500' :
                          'bg-slate-600'
                        }`} />
                        <span className={`text-sm ${status === 'done' ? 'text-slate-300' : status === 'running' ? 'text-blue-300' : 'text-slate-500'}`}>
                          {shortName}
                        </span>
                        <span className="ml-auto text-xs">
                          {status === 'done' && <span className="text-green-400">✓ Done</span>}
                          {status === 'running' && <span className="text-blue-400 animate-pulse">⟳ Running</span>}
                          {status === 'idle' && running && i > 0 && stepStatus(PIPELINE_STEPS[i-1]) !== 'idle' && (
                            <span className="text-slate-600">Waiting...</span>
                          )}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {pipelineDone ? (
                <div className="flex gap-2 mt-4">
                  <div className="flex-1 bg-green-900/30 border border-green-500/30 rounded-xl px-4 py-3 text-center">
                    <p className="text-green-400 text-sm font-semibold">✓ Mô phỏng hoàn thành</p>
                    <p className="text-slate-500 text-xs mt-0.5">Xem kết quả ở Decision Report bên phải</p>
                  </div>
                  <button
                    onClick={() => { setLaunched(false); setSelected(null) }}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-xl transition-colors"
                  >
                    Chạy lại
                  </button>
                </div>
              ) : (
                <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                  <p className="text-xs text-slate-500 mb-1">
                    {pipelineEvents.length > 0
                      ? pipelineEvents[pipelineEvents.length - 1]?.detail || 'Processing...'
                      : 'Khởi động pipeline...'}
                  </p>
                  <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, (PIPELINE_STEPS.filter(s => stepStatus(s) === 'done').length / PIPELINE_STEPS.length) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
