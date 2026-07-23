import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Database, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { CrawlResults } from '../types'

const CRAWL_SOURCES: { key: string; label: string }[] = [
  { key: 'weather', label: 'Thời tiết (Open-Meteo)' },
  { key: 'aqi', label: 'AQI (OpenAQ)' },
  { key: 'news', label: 'Tin tức (VnExpress RSS)' },
]

export default function CrawlPanel() {
  const [crawlResults, setCrawlResults] = useState<CrawlResults | null>(null)

  const crawl = useMutation({
    mutationFn: () => api.runCrawl(),
    onSuccess: setCrawlResults,
  })

  return (
    <div className="space-y-2">
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
  )
}
