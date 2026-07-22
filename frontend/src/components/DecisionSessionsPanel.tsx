import { useMemo, useState } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Loader2, TrendingUp } from 'lucide-react'
import { api } from '../services/api'
import { useTranslation } from '../i18n/useTranslation'
import type { DecisionSession } from '../types'

const OUTCOME_STYLES: Record<string, string> = {
  improved: 'text-emerald-400', worse: 'text-rose-400', no_change: 'text-on-surface-variant',
}

const FILTER_SELECT_CLASS = 'flex-1 bg-surface-container-high border border-outline-variant rounded text-xs px-2 py-1.5 text-on-surface'

function ScoreRow({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-on-surface-variant">{label}</span>
      <span className="text-on-surface tabular-nums">{value != null ? Math.round(value) : '—'}</span>
    </div>
  )
}

function fmtTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : '—'
}

function SessionTimeline({ session }: { session: DecisionSession }) {
  const { t } = useTranslation()
  const steps: [string, string | null][] = [
    [t('sessions.submitted'), session.created_at],
    [session.status === 'rejected' ? t('sessions.statusRejected') : t('sessions.approved'), session.approved_at],
    [t('sessions.observed'), session.observed_at],
    [t('sessions.statusEvaluated'), session.evaluated_at],
  ]
  return (
    <div data-testid="decision-session-timeline" className="flex justify-between text-[9px] text-on-surface-variant pt-1">
      {steps.map(([label, ts]) => (
        <div key={label} className={`text-center ${ts ? 'text-on-surface' : ''}`}>
          <div>{label}</div>
          <div className="tabular-nums">{fmtTime(ts)}</div>
        </div>
      ))}
    </div>
  )
}

function SessionCard({ session }: { session: DecisionSession }) {
  const queryClient = useQueryClient()
  const { t } = useTranslation()
  const statusLabel: Record<string, string> = {
    collecting: t('sessions.statusCollecting'),
    analyzing: t('sessions.statusAnalyzing'),
    recommend: t('sessions.statusRecommend'),
    awaiting_approval: t('sessions.statusAwaitingApproval'),
    rejected: t('sessions.statusRejected'),
    observing: t('sessions.statusObserving'),
    evaluated: t('sessions.statusEvaluated'),
  }
  const observe = useMutation({
    mutationFn: () => api.observeDecisionSession(session.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decision-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['decision-sessions-analytics'] })
    },
  })

  const showOutcome = session.status !== 'collecting' && session.status !== 'analyzing'
    && session.status !== 'recommend' && session.status !== 'awaiting_approval' && session.status !== 'rejected'

  return (
    <div data-testid="decision-session-card" className="bg-surface-container border border-outline-variant rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-on-surface">Session #{session.id}</p>
        <span className="text-[10px] bg-surface-container-high border border-outline-variant text-on-surface-variant rounded-full px-2 py-0.5">
          {statusLabel[session.status] ?? session.status}
        </span>
      </div>
      <p className="text-xs text-on-surface-variant">{session.goal}</p>
      <p className="text-[10px] text-on-surface-variant">{session.run_id}</p>
      <SessionTimeline session={session} />

      {showOutcome && session.baseline_scores && (
        <div className="grid grid-cols-2 gap-3 pt-1 border-t border-outline-variant">
          <div>
            <p className="text-[10px] text-on-surface-variant uppercase mb-1">{t('sessions.baseline')}</p>
            <ScoreRow label={t('sessions.traffic')} value={session.baseline_scores.traffic_score} />
            <ScoreRow label={t('sessions.aqiProxy')} value={session.baseline_scores.environment_score} />
          </div>
          <div>
            <p className="text-[10px] text-on-surface-variant uppercase mb-1">{t('sessions.observed')}</p>
            <ScoreRow label={t('sessions.traffic')} value={session.observed_scores?.traffic_score} />
            <ScoreRow label={t('sessions.aqiProxy')} value={session.observed_scores?.environment_score} />
          </div>
        </div>
      )}

      {session.outcome_status && (
        <div className="flex items-center justify-between pt-1 border-t border-outline-variant text-xs">
          <span className={OUTCOME_STYLES[session.outcome_status]}>
            {session.outcome_delta?.overall_score != null && `${session.outcome_delta.overall_score > 0 ? '+' : ''}${session.outcome_delta.overall_score}`}
            {session.success_rate != null && ` · ${t('sessions.success')} ${session.success_rate}%`}
          </span>
          <span className={`font-semibold ${OUTCOME_STYLES[session.outcome_status]}`}>
            {session.outcome_status === 'improved' ? t('sessions.improved') : session.outcome_status === 'worse' ? t('sessions.outcomeWorse') : t('sessions.outcomeNoChange')}
          </span>
        </div>
      )}

      {session.status === 'observing' && (
        <button
          data-testid="check-outcome-now-button"
          onClick={() => observe.mutate()}
          disabled={observe.isPending}
          className="w-full text-xs bg-primary hover:bg-primary/90 disabled:opacity-50 text-on-primary rounded py-1.5 flex items-center justify-center gap-1.5"
        >
          {observe.isPending ? <Loader2 size={12} className="animate-spin" /> : null}
          {t('sessions.checkOutcomeNow')}
        </button>
      )}
    </div>
  )
}

export default function DecisionSessionsPanel() {
  const [districtFilter, setDistrictFilter] = useState<number | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const { t } = useTranslation()
  const panelHeader = (
    <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
      <TrendingUp size={15} className="text-primary" /> {t('sessions.panelTitle')}
    </h3>
  )
  const statusLabel: Record<string, string> = {
    collecting: t('sessions.statusCollecting'),
    analyzing: t('sessions.statusAnalyzing'),
    recommend: t('sessions.statusRecommend'),
    awaiting_approval: t('sessions.statusAwaitingApproval'),
    rejected: t('sessions.statusRejected'),
    observing: t('sessions.statusObserving'),
    evaluated: t('sessions.statusEvaluated'),
  }

  const { data: sessions, isLoading, isError } = useQuery({
    queryKey: ['decision-sessions'],
    queryFn: () => api.getDecisionSessions(),
    refetchInterval: 5000,
  })
  const { data: analytics } = useQuery({
    queryKey: ['decision-sessions-analytics'],
    queryFn: api.getDecisionSessionAnalytics,
    refetchInterval: 10000,
  })
  const { data: districts } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })

  const sessionDistrictIds = useMemo(
    () => Array.from(new Set((sessions ?? []).map(s => s.district_id).filter((id): id is number => id != null))),
    [sessions],
  )
  const sessionStatuses = useMemo(
    () => Array.from(new Set((sessions ?? []).map(s => s.status))),
    [sessions],
  )
  const filteredSessions = useMemo(
    () => (sessions ?? []).filter(s =>
      (districtFilter === 'all' || s.district_id === districtFilter)
      && (statusFilter === 'all' || s.status === statusFilter),
    ),
    [sessions, districtFilter, statusFilter],
  )

  if (isLoading) {
    return (
      <div className="bg-surface-container border border-outline-variant rounded-lg p-4 space-y-3">
        {panelHeader}
        <div data-testid="decision-sessions-loading" className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-surface-container border border-outline-variant rounded-lg p-4 space-y-3">
        {panelHeader}
        <div data-testid="decision-sessions-error" className="text-error text-sm py-4 text-center">
          {t('common.loadError')}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-surface-container border border-outline-variant rounded-lg p-4 space-y-3">
      {panelHeader}

      {analytics && (
        <div data-testid="decision-analytics" className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-surface-container-high rounded p-2">
            <p className="text-sm font-bold text-on-surface">{analytics.total_sessions}</p>
            <p className="text-[10px] text-on-surface-variant">{t('sessions.sessionsLabel')}</p>
          </div>
          <div className="bg-surface-container-high rounded p-2">
            <p className="text-sm font-bold text-on-surface">{analytics.improved_rate != null ? `${analytics.improved_rate}%` : '—'}</p>
            <p className="text-[10px] text-on-surface-variant">{t('sessions.improved')}</p>
          </div>
          <div className="bg-surface-container-high rounded p-2">
            <p className="text-sm font-bold text-on-surface">{analytics.approval_rate != null ? `${analytics.approval_rate}%` : '—'}</p>
            <p className="text-[10px] text-on-surface-variant">{t('sessions.approval')}</p>
          </div>
        </div>
      )}

      {(sessionDistrictIds.length > 1 || sessionStatuses.length > 1) && (
        <div className="flex gap-2">
          {sessionDistrictIds.length > 1 && (
            <select
              data-testid="decision-sessions-district-filter"
              value={districtFilter}
              onChange={e => setDistrictFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
              className={FILTER_SELECT_CLASS}
            >
              <option value="all">{t('sessions.allDistricts')}</option>
              {sessionDistrictIds.map(id => (
                <option key={id} value={id}>
                  {districts?.find(d => d.id === id)?.name ?? `${t('sessions.districtFallback')} ${id}`}
                </option>
              ))}
            </select>
          )}
          {sessionStatuses.length > 1 && (
            <select
              data-testid="decision-sessions-status-filter"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className={FILTER_SELECT_CLASS}
            >
              <option value="all">{t('sessions.allStatuses')}</option>
              {sessionStatuses.map(status => (
                <option key={status} value={status}>{statusLabel[status] ?? status}</option>
              ))}
            </select>
          )}
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
        {filteredSessions.map(s => <SessionCard key={s.id} session={s} />)}
        {sessions && sessions.length === 0 && (
          <p className="text-xs text-on-surface-variant italic text-center py-4">{t('sessions.noSessionsYet')}</p>
        )}
        {sessions && sessions.length > 0 && filteredSessions.length === 0 && (
          <p className="text-xs text-on-surface-variant italic text-center py-4">{t('sessions.noSessionsMatchFilters')}</p>
        )}
      </div>
    </div>
  )
}
