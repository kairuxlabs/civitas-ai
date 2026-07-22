import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, FileText, Loader2, Search, XCircle } from 'lucide-react'
import { api } from '../../services/api'
import { useTranslation } from '../../i18n/useTranslation'

function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }) : '—'
}

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected'

function reportStatus(r: { requires_approval: boolean; approved: boolean | null }): Exclude<StatusFilter, 'all'> {
  if (r.requires_approval && r.approved === null) return 'pending'
  return r.approved ? 'approved' : 'rejected'
}

export default function ReportsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [actionError, setActionError] = useState<string | null>(null)
  const { data: reports } = useQuery({ queryKey: ['timeline'], queryFn: () => api.getTimeline(50) })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['timeline'] })
  const approve = useMutation({
    mutationFn: (id: number) => api.approveDecision(id),
    onSuccess: () => { setActionError(null); invalidate() },
    onError: () => setActionError(t('reports.actionError')),
  })
  const reject = useMutation({
    mutationFn: (id: number) => api.rejectDecision(id),
    onSuccess: () => { setActionError(null); invalidate() },
    onError: () => setActionError(t('reports.actionError')),
  })

  const filteredReports = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (reports ?? []).filter(r => {
      const matchesSearch = !term || (r.query ?? `${t('reports.reportFallback')} #${r.id}`).toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || reportStatus(r) === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [reports, search, statusFilter, t])

  return (
    <div data-testid="reports-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText size={22} className="text-primary" /> {t('reports.title')}
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          {t('reports.subtitle')}
        </p>
      </div>

      {actionError && (
        <div
          data-testid="reports-action-error"
          className="glass-panel rounded-xl p-3 flex items-center justify-between gap-3 text-error text-sm"
        >
          <span>{actionError}</span>
          <button
            type="button"
            data-testid="reports-action-error-dismiss"
            onClick={() => setActionError(null)}
            className="text-error hover:opacity-70 shrink-0"
          >
            {t('reports.dismiss')}
          </button>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <div className="glass-panel rounded-xl p-2 flex items-center gap-2 flex-1 min-w-[200px]">
          <Search size={16} className="text-outline ml-2" />
          <input
            type="text"
            data-testid="reports-search-input"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t('reports.searchPlaceholder')}
            className="flex-1 bg-transparent text-sm py-1.5 outline-none placeholder:text-outline"
          />
        </div>
        <select
          data-testid="reports-status-filter"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as StatusFilter)}
          className="glass-panel rounded-xl text-sm px-3 py-2 text-on-surface"
        >
          <option value="all">{t('reports.allStatuses')}</option>
          <option value="pending">{t('reports.pending')}</option>
          <option value="approved">{t('reports.approved')}</option>
          <option value="rejected">{t('reports.rejected')}</option>
        </select>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-container-low/50 text-outline text-xs uppercase tracking-wider border-b border-outline-variant">
            <tr>
              <th className="px-6 py-3 font-medium">{t('reports.colReport')}</th>
              <th className="px-6 py-3 font-medium">{t('reports.colConfidence')}</th>
              <th className="px-6 py-3 font-medium">{t('reports.colStatus')}</th>
              <th className="px-6 py-3 font-medium">{t('reports.colCreated')}</th>
              <th className="px-6 py-3 font-medium text-right">{t('reports.colActions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/30">
            {filteredReports.map(r => {
              const pending = reportStatus(r) === 'pending'
              return (
                <tr key={r.id} data-testid="report-row" className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="px-6 py-4">
                    <p className="font-semibold text-on-surface">{r.query ?? `${t('reports.reportFallback')} #${r.id}`}</p>
                    <p className="text-[11px] text-outline">{t('reports.idLabel')} {r.id}</p>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">{r.confidence != null ? `${Math.round(r.confidence)}%` : '—'}</td>
                  <td className="px-6 py-4">
                    {pending ? (
                      <span className="text-outline">{t('reports.pending')}</span>
                    ) : r.approved ? (
                      <span className="text-secondary">{t('reports.approved')}</span>
                    ) : (
                      <span className="text-error">{t('reports.rejected')}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-xs text-outline">{fmtDate(r.created_at)}</td>
                  <td className="px-6 py-4 text-right">
                    {pending && (
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          data-testid="report-approve-button"
                          disabled={approve.isPending}
                          onClick={() => approve.mutate(r.id)}
                          className="p-1.5 text-secondary hover:bg-secondary/10 rounded disabled:opacity-50"
                        >
                          {approve.isPending ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                        </button>
                        <button
                          type="button"
                          data-testid="report-reject-button"
                          disabled={reject.isPending}
                          onClick={() => reject.mutate(r.id)}
                          className="p-1.5 text-error hover:bg-error/10 rounded disabled:opacity-50"
                        >
                          <XCircle size={16} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
            {reports && reports.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-outline italic text-xs">{t('reports.noReportsYet')}</td>
              </tr>
            )}
            {reports && reports.length > 0 && filteredReports.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-outline italic text-xs">{t('reports.noReportsMatchFilters')}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
