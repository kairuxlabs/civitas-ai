// frontend/src/pages/SimulatorPage.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import DecisionPanel from '../components/DecisionPanel'
import type { DecisionOut, SimulationScenario } from '../types'

const SCENARIOS: { id: SimulationScenario; label: string; icon: string; desc: string }[] = [
  { id: 'heavy_rain', label: 'Heavy Rain', icon: '🌧️', desc: '80mm/h rainfall across the district' },
  { id: 'air_pollution', label: 'Air Pollution', icon: '🏭', desc: 'AQI spikes to 200+ hazardous levels' },
  { id: 'major_event', label: 'Major Event', icon: '🎉', desc: '50,000+ attendees in the district' },
  { id: 'heatwave', label: 'Heatwave', icon: '🌡️', desc: 'Temperature exceeds 42°C for 3 days' },
]

export default function SimulatorPage() {
  const [scenario, setScenario] = useState<SimulationScenario | null>(null)
  const [districtId, setDistrictId] = useState(1)
  const [result, setResult] = useState<DecisionOut | null>(null)
  const [loading, setLoading] = useState(false)

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })

  const handleRun = async () => {
    if (!scenario) return
    setLoading(true)
    try {
      const r = await api.simulate(scenario, districtId)
      setResult(r)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">What-if Simulator</h1>
        <p className="text-slate-400 text-sm">Simulate urban stress scenarios and see AI predictions</p>
      </div>

      <div>
        <label className="text-slate-400 text-sm mb-2 block">District</label>
        <select
          value={districtId}
          onChange={e => setDistrictId(Number(e.target.value))}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
        >
          {districts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>

      <div>
        <label className="text-slate-400 text-sm mb-2 block">Scenario</label>
        <div className="grid grid-cols-2 gap-3">
          {SCENARIOS.map(s => (
            <button
              key={s.id}
              onClick={() => setScenario(s.id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                scenario === s.id
                  ? 'border-blue-500 bg-blue-950'
                  : 'border-slate-700 bg-slate-800/50 hover:border-slate-500'
              }`}
            >
              <div className="text-2xl mb-1">{s.icon}</div>
              <div className="font-medium text-slate-200 text-sm">{s.label}</div>
              <div className="text-slate-500 text-xs mt-0.5">{s.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleRun}
        disabled={!scenario || loading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl font-medium transition-colors"
      >
        {loading ? 'Running simulation...' : 'Run Simulation'}
      </button>

      {(result || loading) && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-slate-300 font-medium mb-3">Simulation Results</h3>
          <DecisionPanel decision={result} loading={loading} />
        </div>
      )}
    </div>
  )
}
