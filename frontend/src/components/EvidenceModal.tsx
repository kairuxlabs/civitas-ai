import { X } from 'lucide-react'
import type { EvidenceItem } from '../types'

interface Props {
  evidence: EvidenceItem[]
  onClose: () => void
}

function confidenceColor(confidence: number): string {
  const pct = confidence * 100
  if (pct >= 80) return 'text-green-400'
  if (pct >= 60) return 'text-yellow-400'
  return 'text-red-400'
}

function confidenceBarColor(confidence: number): string {
  const pct = confidence * 100
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 60) return 'bg-yellow-500'
  return 'bg-red-500'
}

function isFreshTimestamp(time: string): boolean {
  return time !== 'static' && !Number.isNaN(Date.parse(time))
}

function groupByAgent(evidence: EvidenceItem[]): [string, EvidenceItem[]][] {
  const groups = new Map<string, EvidenceItem[]>()
  for (const item of evidence) {
    if (!groups.has(item.agent)) groups.set(item.agent, [])
    groups.get(item.agent)!.push(item)
  }
  return Array.from(groups.entries())
}

export default function EvidenceModal({ evidence, onClose }: Props) {
  const groups = groupByAgent(evidence)

  return (
    <div data-testid="evidence-modal" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950 shrink-0">
          <div>
            <p className="text-sm font-bold text-slate-100">Evidence</p>
            <p className="text-xs text-slate-500 mt-0.5">{evidence.length} item(s) supporting this decision</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors p-1">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar space-y-4">
          {groups.length === 0 && (
            <p className="text-xs text-slate-600 text-center py-8">No evidence available for this decision.</p>
          )}
          {groups.map(([agent, items]) => (
            <div key={agent}>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                {agent.charAt(0).toUpperCase() + agent.slice(1)}
              </p>
              <div className="space-y-2">
                {items.map(item => (
                  <div key={item.id} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] bg-slate-700 border border-slate-600 text-slate-300 rounded-full px-2 py-0.5">
                        {item.source}
                      </span>
                      {item.type === 'gap' && (
                        <span data-testid="evidence-gap-badge" className="text-[10px] bg-amber-900 border border-amber-700 text-amber-300 rounded-full px-2 py-0.5">
                          Knowledge Gap
                        </span>
                      )}
                      <span className={`text-xs font-mono font-bold ${confidenceColor(item.confidence)}`}>
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{item.content}</p>
                    {isFreshTimestamp(item.time) && (
                      <p data-testid="evidence-freshness" className="text-[10px] text-slate-500 mt-1">
                        {new Date(item.time).toLocaleString('vi-VN')}
                      </p>
                    )}
                    <div className="h-1 bg-slate-700 rounded-full mt-2">
                      <div
                        className={`h-1 rounded-full ${confidenceBarColor(item.confidence)}`}
                        style={{ width: `${item.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
