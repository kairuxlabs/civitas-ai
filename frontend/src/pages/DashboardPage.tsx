// frontend/src/pages/DashboardPage.tsx
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../services/api'
import DistrictCard from '../components/DistrictCard'
import AlertBanner from '../components/AlertBanner'
import ScoreGauge from '../components/ScoreGauge'
import type { District } from '../types'

export default function DashboardPage() {
  const [selected, setSelected] = useState<number | null>(null)
  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [] } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })

  const cityOverall = scores.length
    ? scores.reduce((acc, s) => acc + s.overall_score, 0) / scores.length
    : 0

  const avgTraffic = scores.length ? scores.reduce((a, s) => a + s.traffic_score, 0) / scores.length : 0
  const avgEnv = scores.length ? scores.reduce((a, s) => a + s.environment_score, 0) / scores.length : 0
  const avgRisk = scores.length ? scores.reduce((a, s) => a + s.risk_score, 0) / scores.length : 0

  const scoreFor = (d: District) => scores.find(s => s.district_id === d.id)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-[1fr_auto] gap-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Hanoi Urban Dashboard</h1>
          <p className="text-slate-400 text-sm">Real-time city intelligence · Auto-refresh 30s</p>
        </div>
        <ScoreGauge score={cityOverall} label="City Score" size="lg" />
      </div>

      <AlertBanner scores={scores} />

      <div className="grid grid-cols-3 gap-4 p-4 bg-slate-900 rounded-xl border border-slate-800">
        <ScoreGauge score={avgTraffic} label="Traffic" />
        <ScoreGauge score={avgEnv} label="Environment" />
        <ScoreGauge score={100 - avgRisk} label="Safety" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {districts.map(d => (
          <DistrictCard
            key={d.id}
            district={d}
            score={scoreFor(d)}
            selected={selected === d.id}
            onClick={() => setSelected(d.id === selected ? null : d.id)}
          />
        ))}
      </div>
    </div>
  )
}
