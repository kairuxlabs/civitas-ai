import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, FileText, Loader2, XCircle } from 'lucide-react'
import { api } from '../../services/api'

function fmtDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }) : '—'
}

export default function ReportsPage() {
  const queryClient = useQueryClient()
  const { data: reports } = useQuery({ queryKey: ['timeline'], queryFn: () => api.getTimeline(50) })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['timeline'] })
  const approve = useMutation({ mutationFn: (id: number) => api.approveDecision(id), onSuccess: invalidate })
  const reject = useMutation({ mutationFn: (id: number) => api.rejectDecision(id), onSuccess: invalidate })

  return (
    <div data-testid="reports-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText size={22} className="text-primary" /> Decision Reports
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Real decision history from the agent pipeline — approve or reject items awaiting review.
        </p>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-container-low/50 text-outline text-xs uppercase tracking-wider border-b border-outline-variant">
            <tr>
              <th className="px-6 py-3 font-medium">Report</th>
              <th className="px-6 py-3 font-medium">Confidence</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Created</th>
              <th className="px-6 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/30">
            {(reports ?? []).map(r => {
              const pending = r.requires_approval && r.approved === null
              return (
                <tr key={r.id} data-testid="report-row" className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="px-6 py-4">
                    <p className="font-semibold text-on-surface">{r.query ?? `Report #${r.id}`}</p>
                    <p className="text-[11px] text-outline">ID: {r.id}</p>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">{r.confidence != null ? `${Math.round(r.confidence)}%` : '—'}</td>
                  <td className="px-6 py-4">
                    {pending ? (
                      <span className="text-outline">Pending</span>
                    ) : r.approved ? (
                      <span className="text-secondary">Approved</span>
                    ) : (
                      <span className="text-error">Rejected</span>
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
                <td colSpan={5} className="px-6 py-8 text-center text-outline italic text-xs">No decision reports yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
