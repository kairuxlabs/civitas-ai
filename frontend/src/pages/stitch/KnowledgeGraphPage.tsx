import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Network, Search, Share2 } from 'lucide-react'
import { api } from '../../services/api'
import { useTranslation } from '../../i18n/useTranslation'

function FilterChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      data-testid="knowledge-label-filter"
      onClick={onClick}
      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
        active
          ? 'bg-primary/20 border-primary text-primary font-semibold'
          : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-high'
      }`}
    >
      {label}
    </button>
  )
}

export default function KnowledgeGraphPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [activeLabel, setActiveLabel] = useState<string | null>(null)

  const { data: summary, isLoading, isError } = useQuery({
    queryKey: ['knowledge-summary', search],
    queryFn: () => api.getKnowledgeSummary(search || undefined),
  })

  const labels = useMemo(
    () => Array.from(new Set((summary?.sample ?? []).map(item => item.label).filter((l): l is string => !!l))),
    [summary],
  )
  const visibleSample = useMemo(
    () => (activeLabel ? (summary?.sample ?? []).filter(item => item.label === activeLabel) : summary?.sample ?? []),
    [summary, activeLabel],
  )

  function handleSearchChange(value: string) {
    setActiveLabel(null)
    setSearch(value)
  }

  return (
    <div data-testid="knowledge-graph-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Share2 size={22} className="text-primary" /> {t('knowledge.title')}
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          {t('knowledge.subtitle')}
        </p>
      </div>

      <div className="glass-panel rounded-xl p-2 flex items-center gap-2">
        <Search size={16} className="text-outline ml-2" />
        <input
          type="text"
          data-testid="knowledge-search-input"
          value={search}
          onChange={e => handleSearchChange(e.target.value)}
          placeholder={t('knowledge.searchPlaceholder')}
          className="flex-1 bg-transparent text-sm py-2 outline-none placeholder:text-outline"
        />
      </div>

      {isLoading && (
        <div data-testid="knowledge-graph-loading" className="flex items-center justify-center py-16">
          <Loader2 size={28} className="animate-spin text-primary" />
        </div>
      )}

      {isError && (
        <div data-testid="knowledge-graph-error" className="glass-panel rounded-xl p-6 text-error text-sm">
          {t('common.loadError')}
        </div>
      )}

      {!isLoading && !isError && (
        <>
          {labels.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <FilterChip label={t('knowledge.filterAll')} active={activeLabel === null} onClick={() => setActiveLabel(null)} />
              {labels.map(label => (
                <FilterChip key={label} label={label} active={activeLabel === label} onClick={() => setActiveLabel(label)} />
              ))}
            </div>
          )}

          {!summary?.configured && (
            <div className="glass-panel rounded-xl p-6 text-sm text-on-surface-variant">
              {t('knowledge.notConfigured1')} <span className="text-tertiary font-semibold">{t('knowledge.notConfiguredWord')}</span> {t('knowledge.notConfigured2')}<code className="text-xs">NEO4J_URI</code> {t('knowledge.notConfigured3')}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
            <div className="glass-panel rounded-xl p-6 flex flex-col items-center justify-center gap-2">
              <Network size={28} className="text-primary" />
              <span data-testid="knowledge-entity-count" className="text-4xl font-black">{summary?.entities ?? 0}</span>
              <span className="text-xs text-outline uppercase tracking-wide">{t('knowledge.entities')}</span>
            </div>
            <div className="glass-panel rounded-xl p-6 flex flex-col items-center justify-center gap-2">
              <Share2 size={28} className="text-secondary" />
              <span data-testid="knowledge-relation-count" className="text-4xl font-black">{summary?.relations ?? 0}</span>
              <span className="text-xs text-outline uppercase tracking-wide">{t('knowledge.relations')}</span>
            </div>
          </div>

          {summary && summary.sample.length > 0 && (
            <div className="glass-panel rounded-xl overflow-hidden">
              <div className="p-4 border-b border-outline-variant bg-surface-container-low">
                <h3 className="text-sm font-semibold">{t('knowledge.sampleConnectedEntities')}</h3>
              </div>
              {visibleSample.length === 0 ? (
                <p className="px-6 py-8 text-center text-outline italic text-xs">{t('knowledge.noEntitiesMatchFilter')}</p>
              ) : (
                <div className="divide-y divide-outline-variant/30">
                  {visibleSample.map((item, i) => (
                    <div key={i} data-testid="knowledge-sample-row" className="px-6 py-3 flex items-center justify-between text-sm">
                      <div>
                        <span className="font-semibold">{item.name}</span>
                        <span className="text-outline text-xs ml-2">{item.label}</span>
                      </div>
                      {item.relation && item.related_name && (
                        <span className="text-xs text-on-surface-variant">
                          {item.relation} → {item.related_name}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
