import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, LineChart, History, Database, Share2,
  Building2, FileBarChart, Settings, Rocket,
} from 'lucide-react'

const NAV: { to: string; label: string; icon: typeof LayoutDashboard; end?: boolean }[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/workspace', label: 'Decision Workspace', icon: LineChart },
  { to: '/sessions', label: 'Decision Sessions', icon: History },
  { to: '/data-sources', label: 'Data Sources', icon: Database },
  { to: '/knowledge', label: 'Knowledge Graph', icon: Share2 },
  { to: '/intelligence', label: 'City Intelligence', icon: Building2 },
  { to: '/reports', label: 'Reports', icon: FileBarChart },
  { to: '/settings', label: 'Settings', icon: Settings },
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
  return (
    <div data-testid="app-shell" className="min-h-screen bg-background text-on-surface">
      <aside className="h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col z-50">
        <div className="px-6 py-5">
          <div className="text-xl font-bold text-primary">Civitas AI</div>
          <div className="text-[10px] text-on-surface-variant mt-0.5">Hanoi City System Operator</div>
        </div>
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={navClass}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-outline-variant">
          <button
            type="button"
            onClick={() => navigate('/workspace')}
            className="w-full bg-primary text-on-primary font-semibold py-2.5 rounded-lg hover:brightness-110 transition flex items-center justify-center gap-2 text-sm"
          >
            <Rocket size={16} /> Run Decision
          </button>
          <p className="text-[10px] text-secondary flex items-center gap-1.5 mt-3 px-1">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            AI Runtime: Active
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
