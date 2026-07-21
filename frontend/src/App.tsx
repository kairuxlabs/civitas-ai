import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from './layout/AppShell'
import OverviewPage from './pages/stitch/OverviewPage'
import DecisionWorkspacePage from './pages/stitch/DecisionWorkspacePage'
import DecisionSessionsPage from './pages/stitch/DecisionSessionsPage'
import CommandCenterRoute from './pages/stitch/CommandCenterRoute'
import MockStitchPage from './pages/stitch/MockStitchPage'

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
            <Route path="command-center" element={<CommandCenterRoute />} />
            <Route path="data-sources" element={<MockStitchPage title="Data Sources" blurb="Ingestion health and pipeline status (mock)." />} />
            <Route path="knowledge" element={<MockStitchPage title="Knowledge Graph" blurb="Neo4j entity explorer (mock layout)." />} />
            <Route path="intelligence" element={<MockStitchPage title="City Intelligence" blurb="District score deep-dive (mock layout)." />} />
            <Route path="reports" element={<MockStitchPage title="Reports" blurb="Decision report archive (mock layout)." />} />
            <Route path="settings" element={<MockStitchPage title="Settings" blurb="Platform configuration (mock layout)." />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
