// frontend/src/pages/CopilotPage.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import DecisionPanel from '../components/DecisionPanel'
import type { DecisionOut, District } from '../types'

export default function CopilotPage() {
  const [query, setQuery] = useState('')
  const [districtId, setDistrictId] = useState<number>(1)
  const [result, setResult] = useState<DecisionOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{ q: string; r: DecisionOut }[]>([])

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await api.chat(query, districtId)
      setResult(r)
      setHistory(prev => [{ q: query, r }, ...prev.slice(0, 4)])
      setQuery('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">AI Copilot</h1>
        <p className="text-slate-400 text-sm">Ask HanoiOS anything about the city</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <select
          value={districtId}
          onChange={e => setDistrictId(Number(e.target.value))}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
        >
          {districts.map((d: District) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="What is the current urban situation in this district?"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? '...' : 'Ask'}
          </button>
        </div>
      </form>

      {(result || loading) && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <DecisionPanel decision={result} loading={loading} />
        </div>
      )}

      {history.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-slate-400 text-xs uppercase tracking-wider">Recent Queries</h3>
          {history.map((h, i) => (
            <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
              <p className="text-slate-300 text-sm font-medium mb-1">{h.q}</p>
              <p className="text-slate-500 text-xs">{h.r.recommendations[0]}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
