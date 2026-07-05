import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CommandCenterPage from './pages/CommandCenterPage'
import MissionControlPage from './pages/MissionControlPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15000, retry: 1 } },
})

type View = 'command' | 'runtime'

export default function App() {
  const [view, setView] = useState<View>('command')

  return (
    <QueryClientProvider client={queryClient}>
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
        * { box-sizing: border-box; }
        html, body, #root { height: 100%; margin: 0; padding: 0; }
      `}</style>
      <div className="h-full flex flex-col bg-slate-950">
        <nav className="flex items-center gap-1 px-3 py-1.5 bg-slate-900 border-b border-slate-800 shrink-0">
          <span className="text-xs font-bold text-cyan-400 tracking-widest mr-3">CITYOS</span>
          <button
            onClick={() => setView('command')}
            className={`text-xs px-3 py-1 rounded ${view === 'command' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Command Center
          </button>
          <button
            onClick={() => setView('runtime')}
            className={`text-xs px-3 py-1 rounded ${view === 'runtime' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Mission Control v2
          </button>
        </nav>
        <div className="flex-1 min-h-0">
          {view === 'command' ? <CommandCenterPage /> : <MissionControlPage />}
        </div>
      </div>
    </QueryClientProvider>
  )
}
