import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, AlertTriangle, Brain, CheckCircle, Clock, Layers, Loader2,
  MapPin, Rocket, ShieldAlert, XCircle,
} from 'lucide-react'
import HanoiMap, { type MapMetric } from '../../components/HanoiMap'
import SimulationPanel from '../../components/SimulationPanel'
import { api } from '../../services/api'
import { averageOverallScore } from '../../utils/scores'
import { useTranslation } from '../../i18n/useTranslation'
import type { RuntimeRun, RuntimeTask } from '../../types'

const ACTIVE_STATUSES = new Set([
  'planning',
  'running',
  'reflecting',
  'deciding',
  'executing_workflow',
])

const RISK_STYLES: Record<string, string> = {
  low: 'bg-secondary/10 text-secondary border-secondary/20',
  medium: 'bg-tertiary/10 text-tertiary border-tertiary/20',
  high: 'bg-error/10 text-error border-error/20',
}

function fmtTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'
}

export default function DecisionWorkspacePage() {
  const { t } = useTranslation()
  const [goal, setGoal] = useState('')
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [selectedDistrict, setSelectedDistrict] = useState(1)
  const [mapMetric, setMapMetric] = useState<MapMetric>('overall_score')
  const queryClient = useQueryClient()

  const goalPresets = [
    t('workspace.goalPreset1'),
    t('workspace.goalPreset2'),
    t('workspace.goalPreset3'),
  ]

  const mapMetrics: { key: MapMetric; label: string }[] = [
    { key: 'overall_score', label: t('workspace.metricOverall') },
    { key: 'traffic_score', label: t('workspace.metricTraffic') },
    { key: 'environment_score', label: t('workspace.metricEnvironment') },
    { key: 'risk_score', label: t('workspace.metricRisk') },
  ]

  const riskLabel: Record<string, string> = {
    low: t('workspace.riskLow'),
    medium: t('workspace.riskMedium'),
    high: t('workspace.riskHigh'),
  }

  const { data: run } = useQuery<RuntimeRun>({
    queryKey: ['v2-run', activeRunId],
    queryFn: () => api.getRun(activeRunId!),
    enabled: Boolean(activeRunId),
    refetchInterval: query => {
      const status = query.state.data?.status
      if (status && ACTIVE_STATUSES.has(status)) return 1200
      return status === 'awaiting_approval' ? 4000 : false
    },
  })
  const { data: runs } = useQuery({
    queryKey: ['v2-runs'],
    queryFn: api.getRuns,
    refetchInterval: 5000,
  })
  const { data: monitor } = useQuery({
    queryKey: ['v2-monitor'],
    queryFn: api.getRuntimeMonitor,
    refetchInterval: 5000,
  })
  const { data: scores } = useQuery({
    queryKey: ['scores'],
    queryFn: api.getScores,
    refetchInterval: 15000,
  })
  const { data: districts } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: aqiHistory } = useQuery({
    queryKey: ['aqi-history', selectedDistrict],
    queryFn: () => api.getAQIHistory(selectedDistrict, 1),
  })

  const submit = useMutation({
    mutationFn: (newGoal: string) => api.submitGoal(newGoal, selectedDistrict),
    onSuccess: submittedRun => {
      setActiveRunId(submittedRun.run_id)
      queryClient.setQueryData(['v2-run', submittedRun.run_id], submittedRun)
      queryClient.invalidateQueries({ queryKey: ['v2-runs'] })
      queryClient.invalidateQueries({ queryKey: ['decision-sessions'] })
    },
  })
  const resolve = useMutation({
    mutationFn: (approved: boolean) => api.resolveRun(activeRunId!, approved),
    onSuccess: resolvedRun => {
      queryClient.setQueryData(['v2-run', activeRunId], resolvedRun)
      queryClient.invalidateQueries({ queryKey: ['decision-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['decision-sessions-analytics'] })
    },
  })

  const avgOverall = useMemo(() => averageOverallScore(scores), [scores])
  const selectedScore = scores?.find(score => score.district_id === selectedDistrict)
  const runDistrictName = districts?.find(d => d.id === run?.district_id)?.name
  const latestAqi = aqiHistory && aqiHistory.length > 0 ? aqiHistory[aqiHistory.length - 1] : null

  function submitGoal(value: string) {
    const trimmedGoal = value.trim()
    if (trimmedGoal.length >= 3) submit.mutate(trimmedGoal)
  }

  return (
    <div data-testid="decision-workspace-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className={`space-y-3 ${run ? 'border-l-4 border-primary pl-4 py-2 bg-surface-container/20 rounded-r-xl' : ''}`}>
        <p className="text-[10px] uppercase tracking-widest text-primary font-semibold">
          {run ? `${t('workspace.activeMission')} ${run.run_id}` : t('workspace.noActiveMission')}
        </p>
        <h1 className="text-2xl font-bold tracking-tight">{run?.goal ?? t('workspace.title')}</h1>

        {run && (
          <div className="flex flex-wrap gap-2">
            {runDistrictName && (
              <span className="text-xs px-2.5 py-1 rounded border border-outline-variant text-on-surface-variant flex items-center gap-1.5">
                <MapPin size={12} /> {runDistrictName}
              </span>
            )}
            {run.decision?.risk && (
              <span className={`text-xs px-2.5 py-1 rounded border flex items-center gap-1.5 ${RISK_STYLES[run.decision.risk]}`}>
                <ShieldAlert size={12} /> {riskLabel[run.decision.risk]} {t('workspace.riskSuffix')}
              </span>
            )}
            <span className="text-xs px-2.5 py-1 rounded border border-outline-variant text-on-surface-variant flex items-center gap-1.5">
              <Clock size={12} /> {t('workspace.started')} {fmtTime(run.created_at)}
            </span>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <input
            value={goal}
            onChange={event => setGoal(event.target.value)}
            onKeyDown={event => event.key === 'Enter' && submitGoal(goal)}
            placeholder={t('workspace.goalPlaceholder')}
            className="flex-1 min-w-[240px] bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <button
            type="button"
            disabled={goal.trim().length < 3 || submit.isPending}
            onClick={() => submitGoal(goal)}
            className="bg-primary text-on-primary font-semibold text-sm px-4 py-2 rounded-lg disabled:opacity-40 flex items-center gap-2"
          >
            {submit.isPending ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
            {t('workspace.executeDecision')}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {goalPresets.map(preset => (
            <button
              key={preset}
              type="button"
              onClick={() => {
                setGoal(preset)
                submitGoal(preset)
              }}
              className="text-xs bg-surface-container-high hover:bg-surface-bright border border-outline-variant text-on-surface-variant px-2.5 py-1 rounded-full"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      <SimulationPanel />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <section className="xl:col-span-3 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2 text-sm">
              <Activity size={16} className="text-primary" /> {t('workspace.executionTrace')}
            </h2>
            {run && ACTIVE_STATUSES.has(run.status) && (
              <span className="text-[10px] text-secondary border border-secondary/30 bg-secondary/10 px-2 py-0.5 rounded-full">
                {t('workspace.live')}
              </span>
            )}
          </div>
          <p className="text-[10px] uppercase text-on-surface-variant">
            {t('workspace.runtimePrefix')} {monitor?.active_runs ?? 0} {t('workspace.active')} / {monitor?.total_runs ?? 0} {t('workspace.total')}
          </p>
          <ul className="space-y-0">
            {(run?.tasks ?? []).map((task: RuntimeTask, index) => (
              <li key={task.id} className="relative pl-7 pb-4 last:pb-0">
                {index < (run?.tasks.length ?? 0) - 1 && (
                  <span className="absolute left-[10px] top-5 bottom-0 w-px bg-outline-variant" />
                )}
                <span className="absolute left-0 top-0.5">
                  {task.status === 'done' ? <CheckCircle size={20} className="text-primary bg-background rounded-full" />
                    : task.status === 'failed' ? <AlertTriangle size={20} className="text-tertiary bg-background rounded-full" />
                      : task.status === 'running' ? <Loader2 size={20} className="text-primary animate-spin bg-background rounded-full" />
                        : <span className="block w-5 h-5 rounded-full border border-outline-variant bg-background" />}
                </span>
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-on-surface">{index + 1}. {task.agent}</span>
                  <span className="font-mono text-[10px] text-outline">{fmtTime(task.started_at)}</span>
                </div>
                <p className="text-[11px] text-on-surface-variant mt-0.5">
                  {task.status}{task.latency_ms != null ? ` · ${Math.round(task.latency_ms)}ms` : ''}
                </p>
              </li>
            ))}
            {!run?.tasks.length && (
              <li className="text-xs text-on-surface-variant italic">{t('workspace.submitGoalPrompt')}</li>
            )}
          </ul>
          {(run?.reflection?.notes ?? []).length > 0 && (
            <div data-testid="decision-reflection-notes" className="space-y-1.5 pt-3 border-t border-outline-variant">
              <p className="text-[10px] uppercase text-on-surface-variant">{t('workspace.reflectionNotes')}</p>
              <ul className="space-y-1.5">
                {run!.reflection!.notes.map((note, index) => (
                  <li key={index} className="text-xs text-on-surface-variant flex items-start gap-1.5">
                    <Brain size={12} className="text-secondary shrink-0 mt-0.5" /> {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {runs?.length ? (
            <div className="pt-3 border-t border-outline-variant space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
              <p className="text-[10px] uppercase text-on-surface-variant">{t('workspace.recentRuns')}</p>
              {runs.map(recentRun => (
                <button
                  key={recentRun.run_id}
                  type="button"
                  onClick={() => setActiveRunId(recentRun.run_id)}
                  className={`w-full text-left text-xs rounded px-2 py-1.5 ${
                    recentRun.run_id === activeRunId
                      ? 'bg-surface-container-highest text-on-surface'
                      : 'text-on-surface-variant hover:bg-surface-container-high'
                  }`}
                >
                  <div className="truncate">{recentRun.goal}</div>
                  <div className="text-[10px] opacity-70">{recentRun.status}</div>
                </button>
              ))}
            </div>
          ) : null}
        </section>

        <section className="xl:col-span-5 glass-panel rounded-xl overflow-hidden">
          <div className="p-3 border-b border-outline-variant flex items-center justify-between gap-2 flex-wrap">
            <span className="text-sm font-semibold flex items-center gap-2">
              <Layers size={15} className="text-primary" /> {t('workspace.districtMap')}
            </span>
            <div className="flex gap-1.5" data-testid="map-metric-toggle">
              {mapMetrics.map(m => (
                <button
                  key={m.key}
                  type="button"
                  onClick={() => setMapMetric(m.key)}
                  className={`text-[11px] px-2.5 py-1 rounded-full border transition-colors ${
                    mapMetric === m.key
                      ? 'bg-primary/20 border-primary text-primary font-semibold'
                      : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-high'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
          <div className="p-3 bg-surface-container-lowest">
            <HanoiMap
              scores={scores ?? []}
              selectedDistrictId={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
              metric={mapMetric}
            />
          </div>
          {selectedScore && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 p-3 border-t border-outline-variant text-xs">
              <div>{t('workspace.metricTraffic')} <span className="font-mono text-on-surface">{Math.round(selectedScore.traffic_score)}</span></div>
              <div>{t('workspace.metricEnvironment')} <span className="font-mono text-on-surface">{Math.round(selectedScore.environment_score)}</span></div>
              <div>{t('workspace.metricRisk')} <span className="font-mono text-on-surface">{Math.round(selectedScore.risk_score)}</span></div>
              {latestAqi ? (
                <div>{t('workspace.aqi')} <span className="font-mono text-on-surface">{Math.round(latestAqi.aqi_index)}</span></div>
              ) : (
                <div>{t('workspace.metricOverall')} <span className="font-mono text-on-surface">{Math.round(selectedScore.overall_score)}</span></div>
              )}
            </div>
          )}
        </section>

        <section className="xl:col-span-4 space-y-gutter">
          <div className="glass-panel rounded-xl p-4">
            <div className="text-xs text-on-surface-variant mb-3">{t('workspace.cityScore')}</div>
            <div className="flex items-center gap-4">
              <div className="relative w-16 h-16 shrink-0">
                <svg viewBox="0 0 60 60" className="w-full h-full -rotate-90">
                  <circle cx="30" cy="30" r="26" fill="none" stroke="currentColor" className="text-outline-variant" strokeWidth="6" />
                  <circle
                    cx="30" cy="30" r="26" fill="none" stroke="currentColor" className="text-secondary"
                    strokeWidth="6" strokeLinecap="round"
                    strokeDasharray={`${((avgOverall ?? 0) / 100) * (2 * Math.PI * 26)} ${2 * Math.PI * 26}`}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-lg font-bold">{avgOverall ?? '—'}</span>
              </div>
              {selectedScore && (
                <div className="flex-1 space-y-1.5">
                  {([
                    [t('workspace.metricTraffic'), selectedScore.traffic_score],
                    [t('workspace.metricEnvironment'), selectedScore.environment_score],
                    [t('workspace.citizen'), selectedScore.citizen_score],
                  ] as const).map(([label, value]) => (
                    <div key={label}>
                      <div className="flex justify-between text-[11px]">
                        <span className="text-on-surface-variant">{label}</span>
                        <span className="text-secondary">{Math.round(value)}%</span>
                      </div>
                      <div className="w-full bg-outline-variant h-1 rounded-full overflow-hidden">
                        <div className="bg-secondary h-full" style={{ width: `${Math.round(value)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          {run?.decision ? (
            <div className="glass-panel rounded-xl overflow-hidden">
              <div className="p-4 space-y-3">
                <h2 className="text-sm font-bold flex items-center gap-2">
                  <Brain size={16} className="text-primary" /> {t('workspace.runtimeDecision')}
                </h2>
                <p className="text-sm text-on-surface-variant">{run.decision.summary}</p>
                <ul className="space-y-1">
                  {run.decision.recommendation.map((recommendation, index) => (
                    <li key={index} className="text-xs text-on-surface">• {recommendation}</li>
                  ))}
                </ul>
                <div className="grid grid-cols-3 gap-2 pt-2">
                  <div className="bg-surface-container-high/60 rounded-lg p-2 border border-outline-variant">
                    <p className="text-[10px] text-outline">{t('workspace.confidence')}</p>
                    <p className="text-sm font-bold">{Math.round(run.decision.confidence)}%</p>
                  </div>
                  <div className="bg-surface-container-high/60 rounded-lg p-2 border border-outline-variant">
                    <p className="text-[10px] text-outline">{t('workspace.risk')}</p>
                    <p className="text-sm font-bold capitalize">{riskLabel[run.decision.risk]}</p>
                  </div>
                  <div className="bg-surface-container-high/60 rounded-lg p-2 border border-outline-variant">
                    <p className="text-[10px] text-outline">{t('workspace.evidence')}</p>
                    <p className="text-sm font-bold">{run.decision.evidence.length}</p>
                  </div>
                </div>
                {(run.decision.critic_notes ?? []).length > 0 && (
                  <ul data-testid="decision-critic-notes" className="space-y-1 border-t border-outline-variant pt-2">
                    {run.decision.critic_notes!.map((note, index) => (
                      <li key={index} className="text-xs text-tertiary flex items-start gap-1.5">
                        <AlertTriangle size={12} className="shrink-0 mt-0.5" /> {note}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {run.status === 'awaiting_approval' && (
                <div className="flex gap-2 p-4 pt-0">
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(true)}
                    className="flex-1 bg-secondary-container text-on-secondary-container text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <CheckCircle size={14} /> {t('workspace.approve')}
                  </button>
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(false)}
                    className="flex-1 bg-error-container/40 text-error text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <XCircle size={14} /> {t('workspace.reject')}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel rounded-xl p-4 text-xs text-on-surface-variant italic">
              {t('workspace.decisionCardEmpty')}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
