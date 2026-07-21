import { useQuery } from '@tanstack/react-query'
import { Settings as SettingsIcon } from 'lucide-react'
import { api } from '../../services/api'

export default function SettingsPage() {
  const { data: status } = useQuery({ queryKey: ['system-status'], queryFn: api.getSystemStatus })

  return (
    <div data-testid="settings-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <SettingsIcon size={22} className="text-primary" /> Platform Configuration
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Read-only view of the real backend configuration — no editable persistence layer exists yet.
        </p>
      </div>

      <section className="glass-panel rounded-xl p-6">
        <h2 className="text-sm font-semibold mb-4">AI Model Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant">
            <p className="text-xs text-outline uppercase mb-2">Primary Model (Gemini)</p>
            <p data-testid="settings-gemini-model" className="font-mono text-sm text-on-surface">
              {status?.gemini_model ?? '—'}
            </p>
            <div className="flex justify-between mt-3 text-xs">
              <span className="text-outline">Temperature</span>
              <span data-testid="settings-gemini-temperature" className="font-mono text-primary">
                {status?.gemini_temperature ?? '—'}
              </span>
            </div>
            <div className="flex justify-between mt-1 text-xs">
              <span className="text-outline">Configured</span>
              <span className={status?.gemini_configured ? 'text-secondary' : 'text-error'}>
                {status?.gemini_configured ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant">
            <p className="text-xs text-outline uppercase mb-2">OpenRouter Fallback Gateway</p>
            <p className="text-xs mb-2">
              <span className="text-outline">Configured: </span>
              <span className={status?.openrouter_configured ? 'text-secondary' : 'text-error'}>
                {status?.openrouter_configured ? 'Yes' : 'No'}
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
        <h2 className="text-sm font-semibold mb-4">Knowledge Layer</h2>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="flex justify-between p-3 rounded bg-surface-container-low">
            <span className="text-outline">Neo4j</span>
            <span className={status?.neo4j_configured ? 'text-secondary' : 'text-outline'}>
              {status?.neo4j_configured ? 'Configured' : 'Not configured'}
            </span>
          </div>
          <div className="flex justify-between p-3 rounded bg-surface-container-low">
            <span className="text-outline">Qdrant</span>
            <span className={status?.qdrant_configured ? 'text-secondary' : 'text-outline'}>
              {status?.qdrant_configured ? 'Configured' : 'Not configured'}
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}
