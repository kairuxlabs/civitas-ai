import { useQuery } from '@tanstack/react-query'
import { Database, Loader2 } from 'lucide-react'
import { api } from '../../services/api'
import type { SystemStatus } from '../../types'

function sourceRows(status: SystemStatus | undefined) {
  return [
    { name: 'PostgreSQL Database', type: 'Sensor + decision store', configured: status?.database ?? false },
    { name: 'Gemini', type: `Primary reasoning model (${status?.gemini_model ?? '—'})`, configured: status?.gemini_configured ?? false },
    { name: 'Neo4j', type: 'Knowledge graph store', configured: status?.neo4j_configured ?? false },
    { name: 'Qdrant', type: 'Vector search index', configured: status?.qdrant_configured ?? false },
    { name: 'OpenRouter', type: 'Fallback AI gateway', configured: status?.openrouter_configured ?? false },
  ]
}

export default function DataSourcesPage() {
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: api.getHealth, refetchInterval: 15000 })
  const { data: status, isLoading, isError } = useQuery({ queryKey: ['system-status'], queryFn: api.getSystemStatus, refetchInterval: 15000 })

  if (isLoading) {
    return (
      <div data-testid="data-sources-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="data-sources-loading" className="flex items-center justify-center py-24">
          <Loader2 size={28} className="animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div data-testid="data-sources-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="data-sources-error" className="glass-panel rounded-xl p-6 text-error text-sm">
          Failed to load — check your connection.
        </div>
      </div>
    )
  }

  return (
    <div data-testid="data-sources-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Database size={22} className="text-primary" /> Data Sources &amp; Health
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Real integration status — no mock latency or uptime figures, only what the API can actually confirm.
          </p>
        </div>
        <span className="text-xs px-3 py-1.5 rounded-full border border-outline-variant text-on-surface-variant">
          API {health?.status ?? 'checking…'}
        </span>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-4 border-b border-outline-variant bg-surface-container-low">
          <h3 className="text-sm font-semibold">Integration Inventory</h3>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-container-low/50 text-outline text-xs uppercase tracking-wider border-b border-outline-variant">
            <tr>
              <th className="px-6 py-3 font-medium">Source</th>
              <th className="px-6 py-3 font-medium">Role</th>
              <th className="px-6 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/30">
            {sourceRows(status).map(row => (
              <tr key={row.name} data-testid="data-source-row" className="hover:bg-surface-container-high/40 transition-colors">
                <td className="px-6 py-4 font-semibold">{row.name}</td>
                <td className="px-6 py-4 text-on-surface-variant">{row.type}</td>
                <td className="px-6 py-4">
                  <span className={`flex items-center gap-2 ${row.configured ? 'text-secondary' : 'text-outline'}`}>
                    <span className={`w-2 h-2 rounded-full ${row.configured ? 'bg-secondary' : 'bg-outline'}`} />
                    {row.configured ? 'Configured' : 'Not configured'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
