import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, LineChart, History, Database, Share2,
  Building2, FileBarChart, Settings, Rocket,
} from 'lucide-react'
import LogoMark from '../components/LogoMark'
import { useTranslation } from '../i18n/useTranslation'
import { useLanguage } from '../i18n/LanguageContext'
import type { TranslationKey } from '../i18n/en'

const NAV: { to: string; labelKey: TranslationKey; icon: typeof LayoutDashboard; end?: boolean }[] = [
  { to: '/', labelKey: 'nav.overview', icon: LayoutDashboard, end: true },
  { to: '/workspace', labelKey: 'nav.decisionWorkspace', icon: LineChart },
  { to: '/sessions', labelKey: 'nav.decisionSessions', icon: History },
  { to: '/data-sources', labelKey: 'nav.dataSources', icon: Database },
  { to: '/knowledge', labelKey: 'nav.knowledgeGraph', icon: Share2 },
  { to: '/intelligence', labelKey: 'nav.cityIntelligence', icon: Building2 },
  { to: '/reports', labelKey: 'nav.reports', icon: FileBarChart },
  { to: '/settings', labelKey: 'nav.settings', icon: Settings },
]

function navClass({ isActive }: { isActive: boolean }) {
  return [
    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
    isActive
      ? 'bg-secondary-container/20 text-secondary border-r-2 border-secondary font-semibold'
      : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest',
  ].join(' ')
}

export default function AppShell() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { language, setLanguage } = useLanguage()

  return (
    <div data-testid="app-shell" className="min-h-screen bg-background text-on-surface">
      <aside className="h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col z-50">
        <div className="px-6 py-5">
          <div className="flex items-center gap-2 text-xl font-bold text-primary">
            <LogoMark size={22} />
            Civitas AI
          </div>
          <div className="text-[10px] text-on-surface-variant mt-0.5">{t('nav.subtitle')}</div>
        </div>
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar">
          {NAV.map(({ to, labelKey, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={navClass}>
              <Icon size={18} />
              <span>{t(labelKey)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-outline-variant space-y-3">
          <button
            type="button"
            onClick={() => navigate('/workspace')}
            className="w-full bg-primary text-on-primary font-semibold py-2.5 rounded-lg hover:brightness-110 transition flex items-center justify-center gap-2 text-sm"
          >
            <Rocket size={16} /> {t('common.runDecision')}
          </button>
          <div className="flex items-center justify-between px-1">
            <div className="flex gap-1">
              <button
                type="button"
                data-testid="lang-switch-en"
                onClick={() => setLanguage('en')}
                className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                  language === 'en' ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:bg-surface-container-highest'
                }`}
              >
                {t('nav.langEn')}
              </button>
              <button
                type="button"
                data-testid="lang-switch-vi"
                onClick={() => setLanguage('vi')}
                className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                  language === 'vi' ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:bg-surface-container-highest'
                }`}
              >
                {t('nav.langVi')}
              </button>
            </div>
          </div>
          <p className="text-[10px] text-secondary flex items-center gap-1.5 px-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            {t('nav.aiRuntimeActive')}
          </p>
        </div>
      </aside>
      <div className="ml-64 min-h-screen flex flex-col">
        <main className="flex-1 min-h-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
