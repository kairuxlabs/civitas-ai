import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import MapPage from './pages/MapPage'
import CopilotPage from './pages/CopilotPage'
import SimulatorPage from './pages/SimulatorPage'

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
    }`
  return (
    <nav className="flex items-center gap-2 px-6 py-3 border-b border-slate-800 bg-slate-900">
      <span className="text-blue-400 font-bold text-lg mr-6">HanoiOS</span>
      <NavLink to="/" className={linkClass} end>Dashboard</NavLink>
      <NavLink to="/map" className={linkClass}>Live Map</NavLink>
      <NavLink to="/copilot" className={linkClass}>AI Copilot</NavLink>
      <NavLink to="/simulator" className={linkClass}>What-if</NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Nav />
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/copilot" element={<CopilotPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
