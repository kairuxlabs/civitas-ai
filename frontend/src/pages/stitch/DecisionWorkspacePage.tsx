import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, AlertTriangle, Brain, CheckCircle, Loader2, Rocket, XCircle,
} from 'lucide-react'
import HanoiMap from '../../components/HanoiMap'
import { api } from '../../services/api'
import type { RuntimeRun, RuntimeTask } from '../../types'

const GOAL_PRESETS = [
  'Prepare the city for heavy rain tonight',
  'Respond to severe air pollution tomorrow',
  'Ensure safety for the weekend festival at Hoan Kiem',
]

const ACTIVE_STATUSES = new Set([
  'planning',
  'running',
  'reflecting',
  'deciding',
  'executing_workflow',
])

export default function DecisionWorkspacePage() {
  const [goal, setGoal] = useState('')
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [selectedDistrict, setSelectedDistrict] = useState(1)
  const queryClient = useQueryClient()

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

  const avgOverall = useMemo(() => {
    if (!scores?.length) return null
    return Math.round(scores.reduce((sum, score) => sum + score.overall_score, 0) / scores.length)
  }, [scores])
  const selectedScore = scores?.find(score => score.district_id === selectedDistrict)

  function submitGoal(value: string) {
    const trimmedGoal = value.trim()
    if (trimmedGoal.length >= 3) submit.mutate(trimmedGoal)
  }

  return (
    <div data-testid="decision-workspace-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className="space-y-2">
        <p className="text-[10px] uppercase tracking-widest text-on-surface-variant">
          {run ? `Active run: ${run.run_id}` : 'No active mission'}
        </p>
        <h1 className="text-2xl font-bold tracking-tight">{run?.goal ?? 'Decision Workspace'}</h1>
        <div className="flex flex-wrap gap-2">
          <input
            value={goal}
            onChange={event => setGoal(event.target.value)}
            onKeyDown={event => event.key === 'Enter' && submitGoal(goal)}
            placeholder="Reduce congestion after heavy rain…"
            className="flex-1 min-w-[240px] bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
          <button
            type="button"
            disabled={goal.trim().length < 3 || submit.isPending}
            onClick={() => submitGoal(goal)}
            className="bg-primary text-on-primary font-semibold text-sm px-4 py-2 rounded-lg disabled:opacity-40 flex items-center gap-2"
          >
            {submit.isPending ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
            Execute Decision
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {GOAL_PRESETS.map(preset => (
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

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <section className="xl:col-span-3 glass-panel rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2 text-sm">
              <Activity size={16} className="text-primary" /> Execution Trace
            </h2>
            {run && ACTIVE_STATUSES.has(run.status) && (
              <span className="text-[10px] text-secondary border border-secondary/30 bg-secondary/10 px-2 py-0.5 rounded-full">
                Live
              </span>
            )}
          </div>
          <p className="text-[10px] uppercase text-on-surface-variant">
            Runtime: {monitor?.active_runs ?? 0} active / {monitor?.total_runs ?? 0} total
          </p>
          <ul className="space-y-3">
            {(run?.tasks ?? []).map((task: RuntimeTask) => (
              <li key={task.id} className="flex gap-2 text-xs">
                {task.status === 'done' ? <CheckCircle size={14} className="text-primary shrink-0" />
                  : task.status === 'failed' ? <AlertTriangle size={14} className="text-tertiary shrink-0" />
                    : task.status === 'running' ? <Loader2 size={14} className="text-primary animate-spin shrink-0" />
                      : <span className="w-3.5 h-3.5 rounded-full border border-outline-variant shrink-0" />}
                <div>
                  <div className="font-semibold text-on-surface">{task.agent}</div>
                  <div className="text-on-surface-variant">
                    {task.status}{task.latency_ms != null ? ` · ${Math.round(task.latency_ms)}ms` : ''}
                  </div>
                </div>
              </li>
            ))}
            {!run?.tasks.length && (
              <li className="text-xs text-on-surface-variant italic">Submit a goal to start the runtime trace.</li>
            )}
          </ul>
          {runs?.length ? (
            <div className="pt-3 border-t border-outline-variant space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
              <p className="text-[10px] uppercase text-on-surface-variant">Recent runs</p>
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
          <div className="p-3 border-b border-outline-variant text-sm font-semibold">District map</div>
          <div className="p-3 bg-surface-container-lowest">
            <HanoiMap
              scores={scores ?? []}
              selectedDistrictId={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
            />
          </div>
          {selectedScore && (
            <div className="grid grid-cols-2 gap-2 p-3 border-t border-outline-variant text-xs">
              <div>Traffic <span className="font-mono text-on-surface">{Math.round(selectedScore.traffic_score)}</span></div>
              <div>Environment <span className="font-mono text-on-surface">{Math.round(selectedScore.environment_score)}</span></div>
              <div>Risk <span className="font-mono text-on-surface">{Math.round(selectedScore.risk_score)}</span></div>
              <div>Overall <span className="font-mono text-on-surface">{Math.round(selectedScore.overall_score)}</span></div>
            </div>
          )}
        </section>

        <section className="xl:col-span-4 space-y-gutter">
          <div className="glass-panel rounded-xl p-4">
            <div className="text-xs text-on-surface-variant mb-2">City Score</div>
            <div className="text-3xl font-semibold">
              {avgOverall ?? '—'}<span className="text-sm text-on-surface-variant"> / 100</span>
            </div>
          </div>
          {run?.decision ? (
            <div className="glass-panel rounded-xl p-4 space-y-3">
              <h2 className="text-sm font-bold flex items-center gap-2">
                <Brain size={16} className="text-primary" /> Runtime Decision
              </h2>
              <p className="text-sm text-on-surface-variant">{run.decision.summary}</p>
              <ul className="space-y-1">
                {run.decision.recommendation.map((recommendation, index) => (
                  <li key={index} className="text-xs text-on-surface">• {recommendation}</li>
                ))}
              </ul>
              <div className="text-xs text-on-surface-variant">
                Confidence: {Math.round(run.decision.confidence)}%
              </div>
              {run.status === 'awaiting_approval' && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(true)}
                    className="flex-1 bg-secondary-container text-on-secondary-container text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <CheckCircle size={14} /> Approve
                  </button>
                  <button
                    type="button"
                    disabled={resolve.isPending}
                    onClick={() => resolve.mutate(false)}
                    className="flex-1 bg-error-container/40 text-error text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
                  >
                    <XCircle size={14} /> Reject
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel rounded-xl p-4 text-xs text-on-surface-variant italic">
              Decision card appears when the runtime finishes planning.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
