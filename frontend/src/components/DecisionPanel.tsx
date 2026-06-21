// frontend/src/components/DecisionPanel.tsx
import type { DecisionOut } from '../types'

interface Props { decision: DecisionOut | null; loading?: boolean }

export default function DecisionPanel({ decision, loading }: Props) {
  if (loading) return (
    <div className="animate-pulse space-y-3">
      {[1,2,3].map(i => <div key={i} className="h-4 bg-slate-700 rounded" />)}
    </div>
  )
  if (!decision) return <p className="text-slate-500 text-sm">No analysis yet.</p>

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-slate-400 text-sm">Confidence</span>
        <div className="flex-1 h-2 bg-slate-700 rounded-full">
          <div
            className="h-2 bg-blue-500 rounded-full transition-all"
            style={{ width: `${decision.confidence}%` }}
          />
        </div>
        <span className="text-blue-400 font-bold text-sm">{Math.round(decision.confidence)}%</span>
      </div>

      <div>
        <h4 className="text-slate-300 font-medium text-sm mb-2">Recommendations</h4>
        <ul className="space-y-1">
          {decision.recommendations.map((r, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <span className="text-blue-400 mt-0.5">→</span>{r}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h4 className="text-slate-300 font-medium text-sm mb-2">Explanation</h4>
        <ul className="space-y-1">
          {decision.explanation.map((e, i) => (
            <li key={i} className="text-xs text-slate-400">{e}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
