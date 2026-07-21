import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Loader2, TrendingUp } from 'lucide-react'
import { api } from '../services/api'
import type { DecisionSession } from '../types'

const STATUS_LABEL: Record<string, string> = {
  collecting: 'Đang thu thập', analyzing: 'Đang phân tích', recommend: 'Đang đề xuất',
  awaiting_approval: 'Chờ phê duyệt', rejected: 'Đã từ chối',
  observing: 'Đang theo dõi', evaluated: 'Đã đánh giá',
}

const OUTCOME_STYLES: Record<string, string> = {
  improved: 'text-emerald-400', worse: 'text-rose-400', no_change: 'text-slate-400',
}

function ScoreRow({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-300 tabular-nums">{value != null ? Math.round(value) : '—'}</span>
    </div>
  )
}

function fmtTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—'
}

function SessionTimeline({ session }: { session: DecisionSession }) {
  const steps: [string, string | null][] = [
    ['Submitted', session.created_at],
    [session.status === 'rejected' ? 'Rejected' : 'Approved', session.approved_at],
    ['Observed', session.observed_at],
    ['Evaluated', session.evaluated_at],
  ]
  return (
    <div data-testid="decision-session-timeline" className="flex justify-between text-[9px] text-slate-600 pt-1">
      {steps.map(([label, ts]) => (
        <div key={label} className={`text-center ${ts ? 'text-slate-400' : ''}`}>
          <div>{label}</div>
          <div className="tabular-nums">{fmtTime(ts)}</div>
        </div>
      ))}
    </div>
  )
}

function SessionCard({ session }: { session: DecisionSession }) {
  const queryClient = useQueryClient()
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
    <div data-testid="decision-session-card" className="bg-slate-900 border border-slate-700 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-200">Session #{session.id}</p>
        <span className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 rounded-full px-2 py-0.5">
          {STATUS_LABEL[session.status] ?? session.status}
        </span>
      </div>
      <p className="text-xs text-slate-400">{session.goal}</p>
      <p className="text-[10px] text-slate-600">{session.run_id}</p>
      <SessionTimeline session={session} />

      {showOutcome && session.baseline_scores && (
        <div className="grid grid-cols-2 gap-3 pt-1 border-t border-slate-800">
          <div>
            <p className="text-[10px] text-slate-600 uppercase mb-1">Baseline</p>
            <ScoreRow label="Traffic" value={session.baseline_scores.traffic_score} />
            <ScoreRow label="AQI proxy" value={session.baseline_scores.environment_score} />
          </div>
          <div>
            <p className="text-[10px] text-slate-600 uppercase mb-1">Observed</p>
            <ScoreRow label="Traffic" value={session.observed_scores?.traffic_score} />
            <ScoreRow label="AQI proxy" value={session.observed_scores?.environment_score} />
          </div>
        </div>
      )}

      {session.outcome_status && (
        <div className="flex items-center justify-between pt-1 border-t border-slate-800 text-xs">
          <span className={OUTCOME_STYLES[session.outcome_status]}>
            {session.outcome_delta?.overall_score != null && `${session.outcome_delta.overall_score > 0 ? '+' : ''}${session.outcome_delta.overall_score}`}
            {session.success_rate != null && ` · Success ${session.success_rate}%`}
          </span>
          <span className={`font-semibold ${OUTCOME_STYLES[session.outcome_status]}`}>
            {session.outcome_status === 'improved' ? 'Improved' : session.outcome_status === 'worse' ? 'Worse' : 'No change'}
          </span>
        </div>
      )}

      {session.status === 'observing' && (
        <button
          data-testid="check-outcome-now-button"
          onClick={() => observe.mutate()}
          disabled={observe.isPending}
          className="w-full text-xs bg-cyan-800 hover:bg-cyan-700 disabled:opacity-50 text-white rounded py-1.5 flex items-center justify-center gap-1.5"
        >
          {observe.isPending ? <Loader2 size={12} className="animate-spin" /> : null}
          Check Outcome Now
        </button>
      )}
    </div>
  )
}

export default function DecisionSessionsPanel() {
  const { data: sessions } = useQuery({
    queryKey: ['decision-sessions'],
    queryFn: () => api.getDecisionSessions(),
    refetchInterval: 5000,
  })
  const { data: analytics } = useQuery({
    queryKey: ['decision-sessions-analytics'],
    queryFn: api.getDecisionSessionAnalytics,
    refetchInterval: 10000,
  })

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
        <TrendingUp size={15} className="text-cyan-400" /> Decision Sessions
      </h3>

      {analytics && (
        <div data-testid="decision-analytics" className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-slate-800 rounded p-2">
            <p className="text-sm font-bold text-slate-200">{analytics.total_sessions}</p>
            <p className="text-[10px] text-slate-500">Sessions</p>
          </div>
          <div className="bg-slate-800 rounded p-2">
            <p className="text-sm font-bold text-slate-200">{analytics.improved_rate != null ? `${analytics.improved_rate}%` : '—'}</p>
            <p className="text-[10px] text-slate-500">Improved</p>
          </div>
          <div className="bg-slate-800 rounded p-2">
            <p className="text-sm font-bold text-slate-200">{analytics.approval_rate != null ? `${analytics.approval_rate}%` : '—'}</p>
            <p className="text-[10px] text-slate-500">Approval</p>
          </div>
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
        {(sessions ?? []).map(s => <SessionCard key={s.id} session={s} />)}
        {sessions && sessions.length === 0 && (
          <p className="text-xs text-slate-600 italic text-center py-4">Chưa có decision session nào</p>
        )}
      </div>
    </div>
  )
}
