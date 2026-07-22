import DecisionSessionsPanel from '../../components/DecisionSessionsPanel'
import { useTranslation } from '../../i18n/useTranslation'

export default function DecisionSessionsPage() {
  const { t } = useTranslation()
  return (
    <div data-testid="decision-sessions-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t('sessions.title')}</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          {t('sessions.subtitle')}
        </p>
      </div>
      <DecisionSessionsPanel />
    </div>
  )
}
