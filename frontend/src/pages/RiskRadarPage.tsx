import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { CityScore, District } from '../types'

function riskLabel(score: number): { label: string; color: string; bg: string } {
  if (score >= 60) return { label: 'HIGH', color: 'text-red-400', bg: 'bg-red-950 border-red-800' }
  if (score >= 30) return { label: 'MEDIUM', color: 'text-yellow-400', bg: 'bg-yellow-950 border-yellow-800' }
  return { label: 'LOW', color: 'text-emerald-400', bg: 'bg-emerald-950 border-emerald-800' }
}

export default function RiskRadarPage() {
  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [], isLoading } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })

  const ranked = [...scores].sort((a, b) => b.risk_score - a.risk_score)
  const districtName = (id: number) => districts.find((d: District) => d.id === id)?.name ?? `District ${id}`

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Risk Radar</h1>
        <p className="text-slate-400 text-sm">Districts ranked by risk score — highest first</p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => <div key={i} className="h-16 bg-slate-800 rounded-xl animate-pulse" />)}
        </div>
      ) : (
        <div className="space-y-3">
          {ranked.map((score: CityScore, i: number) => {
            const risk = riskLabel(score.risk_score)
            return (
              <div key={score.id} className={`flex items-center gap-4 px-5 py-4 rounded-xl border ${risk.bg}`}>
                <span className="text-slate-500 text-sm w-6 text-right">{i + 1}</span>
                <div className="flex-1">
                  <p className="font-semibold text-slate-200">{districtName(score.district_id)}</p>
                  <div className="flex gap-4 mt-1 text-xs text-slate-400">
                    <span>Traffic {Math.round(score.traffic_score)}</span>
                    <span>Air {Math.round(score.environment_score)}</span>
                    <span>Citizen {Math.round(score.citizen_score)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold text-lg ${risk.color}`}>{Math.round(score.risk_score)}</p>
                  <p className={`text-xs font-medium ${risk.color}`}>{risk.label}</p>
                </div>
                <div className="w-24">
                  <div className="h-2 bg-slate-700 rounded-full">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        score.risk_score >= 60 ? 'bg-red-500' :
                        score.risk_score >= 30 ? 'bg-yellow-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${score.risk_score}%` }}
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="flex gap-6 text-xs text-slate-500 pt-2">
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"/>High risk (60+)</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-yellow-500 inline-block"/>Medium (30–60)</span>
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"/>Low (&lt;30)</span>
      </div>
    </div>
  )
}
