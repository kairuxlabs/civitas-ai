import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CloudDrizzle, Database, Loader2, Play, Square } from 'lucide-react'
import { api } from '../services/api'
import type { CrawlResults } from '../types'

const CRAWL_SOURCES: { key: string; label: string }[] = [
  { key: 'weather', label: 'Thời tiết (Open-Meteo)' },
  { key: 'aqi', label: 'AQI (OpenAQ)' },
  { key: 'news', label: 'Tin tức (VnExpress RSS)' },
]

export default function SimulationPanel() {
  const [scenario, setScenario] = useState('heavy_rain')
  const [autoGoal, setAutoGoal] = useState(true)
  const [crawlResults, setCrawlResults] = useState<CrawlResults | null>(null)
  const queryClient = useQueryClient()

  const { data: scenarios } = useQuery({ queryKey: ['v2-scenarios'], queryFn: api.getScenarios, staleTime: Infinity })

  const { data: status } = useQuery({
    queryKey: ['v2-sim-status'],
    queryFn: api.getSimulationStatus,
    refetchInterval: q => (q.state.data?.running ? 3000 : 10000),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['v2-sim-status'] })

  const start = useMutation({
    mutationFn: () => api.startSimulation(scenario, 30, autoGoal),
    onSuccess: s => queryClient.setQueryData(['v2-sim-status'], s),
    onSettled: invalidate,
  })
  const stop = useMutation({
    mutationFn: api.stopSimulation,
    onSuccess: s => queryClient.setQueryData(['v2-sim-status'], s),
    onSettled: invalidate,
  })
  const crawl = useMutation({
    mutationFn: () => api.runCrawl(),
    onSuccess: setCrawlResults,
  })

  return (
    <div data-testid="digital-twin-panel" className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
        <CloudDrizzle size={16} className="text-sky-400" /> Digital Twin &amp; Data
      </h3>

      {/* Simulation controls */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={scenario}
          onChange={e => setScenario(e.target.value)}
          disabled={status?.running}
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none"
        >
          {(scenarios ?? [{ name: 'heavy_rain', label: 'Mưa lớn' }]).map(s => (
            <option key={s.name} value={s.name}>{s.label}</option>
          ))}
        </select>
        <label className="text-xs text-slate-400 flex items-center gap-1.5 select-none">
          <input
            type="checkbox"
            checked={autoGoal}
            onChange={e => setAutoGoal(e.target.checked)}
            disabled={status?.running}
            className="accent-cyan-500"
          />
          Tự chạy agent khi vượt ngưỡng
        </label>
        {status?.running ? (
          <button
            data-testid="sim-stop-btn"
            onClick={() => stop.mutate()}
            disabled={stop.isPending}
            className="ml-auto bg-rose-800 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded flex items-center gap-1.5"
          >
            <Square size={12} /> Dừng
          </button>
        ) : (
          <button
            data-testid="sim-start-btn"
            onClick={() => start.mutate()}
            disabled={start.isPending}
            className="ml-auto bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded flex items-center gap-1.5"
          >
            {start.isPending ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />} Bắt đầu
          </button>
        )}
      </div>

      {/* Live status */}
      {status && (
        <div data-testid="sim-status" className="flex flex-wrap items-center gap-2 text-xs">
          <span className={`px-2 py-0.5 rounded-full border ${
            status.running
              ? 'bg-sky-950 text-sky-300 border-sky-700 animate-pulse'
              : 'bg-slate-800 text-slate-500 border-slate-700'
          }`}>
            {status.running ? `Đang mô phỏng: ${status.scenario_label} · tick ${status.tick}` : 'Mô phỏng đang tắt'}
          </span>
          {status.running && (
            <span className="text-slate-400 tabular-nums">
              Mưa {status.values.rain}mm · AQI {status.values.aqi} · {status.values.temperature}°C
            </span>
          )}
          {status.last_auto_goal && (
            <span className="text-emerald-500">Đã tự kích hoạt run: {status.last_auto_goal}</span>
          )}
        </div>
      )}

      {/* Crawl */}
      <div className="border-t border-slate-800 pt-3 space-y-2">
        <div className="flex items-center gap-2">
          <button
            data-testid="sim-crawl-btn"
            onClick={() => crawl.mutate()}
            disabled={crawl.isPending}
            className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded flex items-center gap-1.5"
          >
            {crawl.isPending ? <Loader2 size={12} className="animate-spin" /> : <Database size={12} />}
            Crawl dữ liệu ngay
          </button>
          <span className="text-xs text-slate-600">Open-Meteo · OpenAQ · VnExpress RSS</span>
        </div>
        {crawlResults && (
          <ul data-testid="sim-crawl-results" className="flex flex-wrap gap-2">
            {CRAWL_SOURCES.map(({ key, label }) => {
              const r = crawlResults[key]
              if (!r) return null
              return (
                <li
                  key={key}
                  className={`text-xs px-2 py-0.5 rounded border ${
                    r.ok ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-rose-950 text-rose-300 border-rose-800'
                  }`}
                  title={r.error}
                >
                  {label}: {r.ok ? (r.count != null ? `${r.count} mục` : 'OK') : 'lỗi'}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
