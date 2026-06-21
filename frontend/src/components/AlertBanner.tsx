// frontend/src/components/AlertBanner.tsx
import { AlertTriangle, CheckCircle, Info } from 'lucide-react'
import type { CityScore } from '../types'

interface Props { scores: CityScore[] }

export default function AlertBanner({ scores }: Props) {
  const highRisk = scores.filter(s => s.risk_score > 60)
  const lowEnv = scores.filter(s => s.environment_score < 50)

  const alerts = [
    ...highRisk.map(s => ({ level: 'danger' as const, msg: `High flood risk in district ${s.district_id}` })),
    ...lowEnv.map(s => ({ level: 'warning' as const, msg: `Poor air quality in district ${s.district_id}` })),
    ...(highRisk.length === 0 && lowEnv.length === 0 ? [{ level: 'ok' as const, msg: 'All districts operating normally' }] : []),
  ]

  return (
    <div className="flex flex-col gap-2">
      {alerts.slice(0, 3).map((a, i) => (
        <div key={i} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${
          a.level === 'danger' ? 'bg-red-950 text-red-300 border border-red-800' :
          a.level === 'warning' ? 'bg-yellow-950 text-yellow-300 border border-yellow-800' :
          'bg-emerald-950 text-emerald-300 border border-emerald-800'
        }`}>
          {a.level === 'danger' ? <AlertTriangle size={14} /> :
           a.level === 'warning' ? <Info size={14} /> : <CheckCircle size={14} />}
          {a.msg}
        </div>
      ))}
    </div>
  )
}
