import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from './layout/AppShell'
import OverviewPage from './pages/stitch/OverviewPage'
import DecisionWorkspacePage from './pages/stitch/DecisionWorkspacePage'
import DecisionSessionsPage from './pages/stitch/DecisionSessionsPage'
import DataSourcesPage from './pages/stitch/DataSourcesPage'
import KnowledgeGraphPage from './pages/stitch/KnowledgeGraphPage'
import CityIntelligencePage from './pages/stitch/CityIntelligencePage'
import ReportsPage from './pages/stitch/ReportsPage'
import SettingsPage from './pages/stitch/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15000, retry: 1 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #424754; border-radius: 10px; }
        * { box-sizing: border-box; }
        html, body, #root { height: 100%; margin: 0; padding: 0; }
      `}</style>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<OverviewPage />} />
            <Route path="workspace" element={<DecisionWorkspacePage />} />
            <Route path="sessions" element={<DecisionSessionsPage />} />
            <Route path="data-sources" element={<DataSourcesPage />} />
            <Route path="knowledge" element={<KnowledgeGraphPage />} />
            <Route path="intelligence" element={<CityIntelligencePage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
