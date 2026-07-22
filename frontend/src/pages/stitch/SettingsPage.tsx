import { useQuery } from '@tanstack/react-query'
import { Loader2, Settings as SettingsIcon } from 'lucide-react'
import { api } from '../../services/api'
import { useTranslation } from '../../i18n/useTranslation'

export default function SettingsPage() {
  const { t } = useTranslation()
  const { data: status, isLoading, isError } = useQuery({ queryKey: ['system-status'], queryFn: api.getSystemStatus })

  if (isLoading) {
    return (
      <div data-testid="settings-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="settings-loading" className="flex items-center justify-center py-24">
          <Loader2 size={28} className="animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div data-testid="settings-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="settings-error" className="glass-panel rounded-xl p-6 text-error text-sm">
          {t('common.loadError')}
        </div>
      </div>
    )
  }

  return (
    <div data-testid="settings-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <SettingsIcon size={22} className="text-primary" /> {t('settings.title')}
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          {t('settings.subtitle')}
        </p>
      </div>

      <section className="glass-panel rounded-xl p-6">
        <h2 className="text-sm font-semibold mb-4">{t('settings.aiModelConfig')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant">
            <p className="text-xs text-outline uppercase mb-2">{t('settings.primaryModelGemini')}</p>
            <p data-testid="settings-gemini-model" className="font-mono text-sm text-on-surface">
              {status?.gemini_model ?? '—'}
            </p>
            <div className="flex justify-between mt-3 text-xs">
              <span className="text-outline">{t('settings.temperature')}</span>
              <span data-testid="settings-gemini-temperature" className="font-mono text-primary">
                {status?.gemini_temperature ?? '—'}
              </span>
            </div>
            <div className="flex justify-between mt-1 text-xs">
              <span className="text-outline">{t('settings.configured')}</span>
              <span className={status?.gemini_configured ? 'text-secondary' : 'text-error'}>
                {status?.gemini_configured ? t('common.yes') : t('common.no')}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant">
            <p className="text-xs text-outline uppercase mb-2">{t('settings.openRouterFallback')}</p>
            <p className="text-xs mb-2">
              <span className="text-outline">{t('settings.configuredColon')}</span>
              <span className={status?.openrouter_configured ? 'text-secondary' : 'text-error'}>
                {status?.openrouter_configured ? t('common.yes') : t('common.no')}
              </span>
            </p>
            <ul className="space-y-1">
              {(status?.openrouter_fallback_models ?? []).map(model => (
                <li key={model} data-testid="settings-fallback-model" className="font-mono text-xs text-on-surface-variant">
                  {model}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-xl p-6">
        <h2 className="text-sm font-semibold mb-4">{t('settings.knowledgeLayer')}</h2>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="flex justify-between p-3 rounded bg-surface-container-low">
            <span className="text-outline">Neo4j</span>
            <span className={status?.neo4j_configured ? 'text-secondary' : 'text-outline'}>
              {status?.neo4j_configured ? t('common.configured') : t('common.notConfigured')}
            </span>
          </div>
          <div className="flex justify-between p-3 rounded bg-surface-container-low">
            <span className="text-outline">Qdrant</span>
            <span className={status?.qdrant_configured ? 'text-secondary' : 'text-outline'}>
              {status?.qdrant_configured ? t('common.configured') : t('common.notConfigured')}
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}
