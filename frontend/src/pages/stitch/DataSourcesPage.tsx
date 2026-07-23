import { useQuery } from '@tanstack/react-query'
import { Database, Loader2 } from 'lucide-react'
import { api } from '../../services/api'
import { useTranslation } from '../../i18n/useTranslation'
import CrawlPanel from '../../components/CrawlPanel'
import type { SystemStatus } from '../../types'
import type { TranslationKey } from '../../i18n/en'

function sourceRows(status: SystemStatus | undefined, t: (key: TranslationKey) => string) {
  return [
    { name: 'PostgreSQL Database', type: t('dataSources.typePostgres'), configured: status?.database ?? false },
    { name: 'Gemini', type: `${t('dataSources.typeGeminiPrefix')} (${status?.gemini_model ?? '—'})`, configured: status?.gemini_configured ?? false },
    { name: 'Neo4j', type: t('dataSources.typeNeo4j'), configured: status?.neo4j_configured ?? false },
    { name: 'Qdrant', type: t('dataSources.typeQdrant'), configured: status?.qdrant_configured ?? false },
    { name: 'OpenRouter', type: t('dataSources.typeOpenRouter'), configured: status?.openrouter_configured ?? false },
  ]
}

export default function DataSourcesPage() {
  const { t } = useTranslation()
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
          {t('common.loadError')}
        </div>
      </div>
    )
  }

  return (
    <div data-testid="data-sources-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Database size={22} className="text-primary" /> {t('dataSources.title')}
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">
            {t('dataSources.subtitle')}
          </p>
        </div>
        <span className="text-xs px-3 py-1.5 rounded-full border border-outline-variant text-on-surface-variant">
          {t('dataSources.apiPrefix')} {health?.status ?? t('dataSources.checking')}
        </span>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-4 border-b border-outline-variant bg-surface-container-low">
          <h3 className="text-sm font-semibold">{t('dataSources.integrationInventory')}</h3>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-container-low/50 text-outline text-xs uppercase tracking-wider border-b border-outline-variant">
            <tr>
              <th className="px-6 py-3 font-medium">{t('dataSources.colSource')}</th>
              <th className="px-6 py-3 font-medium">{t('dataSources.colRole')}</th>
              <th className="px-6 py-3 font-medium">{t('dataSources.colStatus')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/30">
            {sourceRows(status, t).map(row => (
              <tr key={row.name} data-testid="data-source-row" className="hover:bg-surface-container-high/40 transition-colors">
                <td className="px-6 py-4 font-semibold">{row.name}</td>
                <td className="px-6 py-4 text-on-surface-variant">{row.type}</td>
                <td className="px-6 py-4">
                  <span className={`flex items-center gap-2 ${row.configured ? 'text-secondary' : 'text-outline'}`}>
                    <span className={`w-2 h-2 rounded-full ${row.configured ? 'bg-secondary' : 'bg-outline'}`} />
                    {row.configured ? t('common.configured') : t('common.notConfigured')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="glass-panel rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-3">{t('dataSources.crawlSectionTitle')}</h3>
        <CrawlPanel />
      </div>
    </div>
  )
}
