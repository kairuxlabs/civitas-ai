import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import {
  BarChart2, Activity, Map as MapIcon, MessageSquare,
  Shield, AlertTriangle, Sliders, Clock
} from 'lucide-react'
import DashboardPage from './pages/DashboardPage'
import MapPage from './pages/MapPage'
import CopilotPage from './pages/CopilotPage'
import SimulatorPage from './pages/SimulatorPage'
import RiskRadarPage from './pages/RiskRadarPage'
import TimelinePage from './pages/TimelinePage'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: BarChart2, end: true },
  { to: '/risk', label: 'Risk Radar', icon: Activity },
  { to: '/map', label: 'City Map', icon: MapIcon },
  { to: '/copilot', label: 'AI Copilot', icon: MessageSquare },
  { to: '/simulator', label: 'What-If', icon: Sliders },
  { to: '/timeline', label: 'Timeline', icon: Clock },
]

function PageTitle() {
  const location = useLocation()
  const item = NAV_ITEMS.find(n => n.end ? location.pathname === '/' : location.pathname.startsWith(n.to))
  return item?.label ?? 'HanoiOS'
}

function Sidebar() {
  return (
    <nav className="fixed top-0 left-0 h-full w-64 bg-slate-950 border-r border-slate-800 flex flex-col z-20">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield className="text-white w-6 h-6" />
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-100">Civitas AI</span>
        </div>

        <div className="space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 border ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border-transparent'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} className={isActive ? 'text-blue-500' : ''} />
                  <span className="font-medium">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>

      <div className="mt-auto p-6 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
            <span className="text-sm font-medium text-slate-300">OP</span>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">Operator 1</p>
            <p className="text-xs text-slate-500">City Command Center</p>
          </div>
        </div>
      </div>
    </nav>
  )
}

function AppHeader() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('vi-VN'))

  useEffect(() => {
    const t = setInterval(() => setTime(new Date().toLocaleTimeString('vi-VN')), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <header className="flex justify-between items-center mb-8 bg-slate-900/80 backdrop-blur-md sticky top-0 py-4 z-10 border-b border-slate-800 -mx-8 px-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 capitalize">
          <PageTitle />
        </h1>
        <p className="text-slate-400 text-sm mt-1">Real-time city operations monitoring</p>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="text-lg font-mono text-slate-200">{time}</p>
          <p className="text-xs text-slate-500">Hanoi, Vietnam (ICT)</p>
        </div>
        <div className="flex gap-3">
          <button className="p-2 rounded-full bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors relative">
            <AlertTriangle size={20} />
            <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-slate-800" />
          </button>
          <button className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors shadow-lg shadow-blue-500/20 text-sm">
            Export Report
          </button>
        </div>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900 text-slate-200 font-sans">
        <style>{`
          .custom-scrollbar::-webkit-scrollbar { width: 6px; }
          .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
          .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
        `}</style>

        <Sidebar />

        <main className="ml-64 p-8 min-h-screen">
          <AppHeader />
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/copilot" element={<CopilotPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/risk" element={<RiskRadarPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
