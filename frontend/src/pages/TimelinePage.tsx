import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { AgentDecisionOut } from '../types'

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) +
    ' ' + d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

function confidenceColor(c: number | null) {
  if (!c) return 'text-slate-500'
  return c >= 80 ? 'text-emerald-400' : c >= 60 ? 'text-yellow-400' : 'text-red-400'
}

export default function TimelinePage() {
  const { data: events = [], isLoading } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => api.getTimeline(30),
    refetchInterval: 15000,
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">AI Timeline</h1>
        <p className="text-slate-400 text-sm">Chronological feed of AI decisions and anomalies — auto-refresh 15s</p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="h-24 bg-slate-800 rounded-xl animate-pulse" />)}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <p className="text-4xl mb-3">⏳</p>
          <p>No decisions recorded yet. Use the AI Copilot or Simulator to generate data.</p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-[1.1rem] top-0 bottom-0 w-px bg-slate-700" />
          <div className="space-y-4">
            {(events as AgentDecisionOut[]).map((ev, i) => (
              <div key={ev.id ?? i} className="flex gap-4 relative">
                <div className="w-8 h-8 rounded-full bg-slate-800 border-2 border-blue-500 flex items-center justify-center text-xs text-blue-400 font-bold shrink-0 z-10">
                  {i + 1}
                </div>
                <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-slate-300 text-sm font-medium">{ev.query ?? 'Automated analysis'}</p>
                    <span className="text-slate-500 text-xs shrink-0">{formatTime(ev.created_at)}</span>
                  </div>
                  {ev.recommendations && ev.recommendations.length > 0 && (
                    <p className="text-slate-400 text-xs">→ {ev.recommendations[0]}</p>
                  )}
                  <div className="flex items-center gap-4 text-xs">
                    <span className={`font-semibold ${confidenceColor(ev.confidence)}`}>
                      Confidence {ev.confidence != null ? Math.round(ev.confidence) + '%' : '—'}
                    </span>
                    {ev.district_id && (
                      <span className="text-slate-500">District {ev.district_id}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
