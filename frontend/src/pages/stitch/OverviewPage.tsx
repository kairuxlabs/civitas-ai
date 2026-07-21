import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Activity, Database, Rocket, ShieldAlert } from 'lucide-react'
import { api } from '../../services/api'
import HanoiMap from '../../components/HanoiMap'

export default function OverviewPage() {
  const navigate = useNavigate()
  const [selectedDistrict, setSelectedDistrict] = useState(1)

  const { data: health } = useQuery({ queryKey: ['health'], queryFn: api.getHealth, refetchInterval: 15000 })
  const { data: districts } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 15000 })
  const { data: analytics } = useQuery({
    queryKey: ['decision-sessions-analytics'],
    queryFn: api.getDecisionSessionAnalytics,
    refetchInterval: 10000,
  })

  const avgOverall = useMemo(() => {
    if (!scores?.length) return null
    return Math.round(scores.reduce((sum, score) => sum + score.overall_score, 0) / scores.length)
  }, [scores])

  return (
    <div data-testid="overview-page" className="p-margin-desktop space-y-gutter pb-16">
      <section className="glass-panel p-6 rounded-xl relative overflow-hidden">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight mb-2">City Status Matrix</h1>
            <p className="text-on-surface-variant max-w-xl text-sm">
              Hanoi Metropolitan Area. {(districts?.length ?? 12)} districts reporting
              {health?.status ? ` · API ${health.status}` : ''}.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/workspace')}
            className="bg-primary text-on-primary text-sm font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shrink-0"
          >
            <Rocket size={16} /> Run Decision
          </button>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-primary">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Overall City Score</span>
            <Activity size={16} className="text-primary" />
          </div>
          <div data-testid="overview-overall-score" className="text-2xl font-semibold">
            {avgOverall ?? '—'}
            <span className="text-sm text-on-surface-variant font-normal"> / 100</span>
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-secondary">
          <div className="text-xs text-on-surface-variant mb-2">Decision Sessions</div>
          <div className="text-2xl font-semibold">{analytics?.total_sessions ?? '—'}</div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-primary-container">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Approval Rate</span>
            <Database size={16} className="text-primary-container" />
          </div>
          <div className="text-2xl font-semibold">
            {analytics?.approval_rate != null ? `${analytics.approval_rate}%` : '—'}
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-tertiary">
          <div className="text-xs text-on-surface-variant mb-2 flex justify-between">
            <span>Improved Rate</span>
            <ShieldAlert size={16} className="text-tertiary" />
          </div>
          <div className="text-2xl font-semibold">
            {analytics?.improved_rate != null ? `${analytics.improved_rate}%` : '—'}
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-xl overflow-hidden">
        <div className="p-4 border-b border-outline-variant flex items-center justify-between">
          <h2 className="font-semibold text-base">Live Intelligence Stream: Hanoi</h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-primary/30 text-primary bg-primary/10">
            LIVE TELEMETRY
          </span>
        </div>
        <div className="p-4 bg-surface-container-lowest">
          <HanoiMap
            scores={scores ?? []}
            selectedDistrictId={selectedDistrict}
            onSelectDistrict={setSelectedDistrict}
          />
        </div>
      </section>
    </div>
  )
}
