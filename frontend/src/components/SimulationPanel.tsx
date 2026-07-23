import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CloudDrizzle, Loader2, Play, Square } from 'lucide-react'
import CrawlPanel from './CrawlPanel'
import { api } from '../services/api'

// Which reading is the actual auto-goal trigger signal for each scenario,
// matching backend/src/simulation/profiles.py's per-scenario goal_trigger.
// major_event/normal have no weather-based trigger (major_event fires on a
// crowd-event probability instead), so neither metric is highlighted for them.
const PRIMARY_METRIC: Record<string, 'rain' | 'aqi' | 'temperature' | null> = {
  normal: null,
  heavy_rain: 'rain',
  air_pollution: 'aqi',
  heatwave: 'temperature',
  major_event: null,
}

function metricClass(metric: 'rain' | 'aqi' | 'temperature', activeScenario: string): string {
  return PRIMARY_METRIC[activeScenario] === metric ? 'text-amber-300 font-semibold' : 'text-slate-400'
}

interface Props {
  districtId?: number
}

export default function SimulationPanel({ districtId = 1 }: Props) {
  const [scenario, setScenario] = useState('heavy_rain')
  const [autoGoal, setAutoGoal] = useState(true)
  const queryClient = useQueryClient()

  const { data: scenarios } = useQuery({ queryKey: ['v2-scenarios'], queryFn: api.getScenarios, staleTime: Infinity })

  const { data: status } = useQuery({
    queryKey: ['v2-sim-status'],
    queryFn: api.getSimulationStatus,
    refetchInterval: q => (q.state.data?.running ? 3000 : 10000),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['v2-sim-status'] })

  const start = useMutation({
    mutationFn: () => api.startSimulation(scenario, 30, autoGoal, districtId),
    onSuccess: s => queryClient.setQueryData(['v2-sim-status'], s),
    onSettled: invalidate,
  })
  const stop = useMutation({
    mutationFn: api.stopSimulation,
    onSuccess: s => queryClient.setQueryData(['v2-sim-status'], s),
    onSettled: invalidate,
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
            <span className="tabular-nums" data-testid="sim-values">
              <span className={metricClass('rain', status.scenario)}>Mưa {status.values.rain}mm</span>
              {' · '}
              <span className={metricClass('aqi', status.scenario)}>AQI {status.values.aqi}</span>
              {' · '}
              <span className={metricClass('temperature', status.scenario)}>{status.values.temperature}°C</span>
            </span>
          )}
          {status.last_auto_goal && (
            <span className="text-emerald-500">Đã tự kích hoạt run: {status.last_auto_goal}</span>
          )}
        </div>
      )}

      {/* Crawl */}
      <div className="border-t border-slate-800 pt-3">
        <CrawlPanel />
      </div>
    </div>
  )
}
