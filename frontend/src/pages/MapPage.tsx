import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { api } from '../services/api'
import type { District, CityScore } from '../types'

// Static district coordinates for Hanoi
const DISTRICT_COORDS: Record<number, [number, number]> = {
  1:  [105.849,  21.028],
  2:  [105.841,  21.035],
  3:  [105.845,  21.022],
  4:  [105.856,  21.018],
  5:  [105.862,  21.008],
  6:  [105.838,  21.012],
  7:  [105.795,  21.025],
  8:  [105.880,  21.038],
  9:  [105.760,  21.015],
  10: [105.770,  21.042],
  11: [105.832,  21.055],
  12: [105.778,  21.005],
}

function scoreColor(score?: number): string {
  if (!score) return '#64748b'
  if (score >= 70) return '#10b981'
  if (score >= 50) return '#f59e0b'
  return '#ef4444'
}

function riskLevel(riskScore: number): { label: string; labelCls: string; bg: string } {
  if (riskScore >= 60) return { label: 'HIGH',   labelCls: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/20' }
  if (riskScore >= 30) return { label: 'MEDIUM', labelCls: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' }
  return                      { label: 'LOW',    labelCls: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
}

export default function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const [selected, setSelected] = useState<{ district: District; score?: CityScore } | null>(null)

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [] } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })

  // Init map once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return
    mapRef.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://tiles.openfreemap.org/styles/dark',
      center: [105.845, 21.025],
      zoom: 11.5,
    })
    mapRef.current.addControl(new maplibregl.NavigationControl(), 'bottom-right')
    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [])

  // Markers
  useEffect(() => {
    if (!mapRef.current || !districts.length) return
    const map = mapRef.current

    markersRef.current.forEach(m => m.remove())
    markersRef.current = []

    districts.forEach(district => {
      const score = scores.find(s => s.district_id === district.id)
      const color = scoreColor(score?.overall_score)
      const [lng, lat] = DISTRICT_COORDS[district.id] ?? [105.845 + (district.id * 0.01) - 0.06, 21.025]

      const el = document.createElement('div')
      el.className = 'district-marker'
      el.style.cssText = `
        width: 36px; height: 36px;
        background: ${color}22;
        border: 2px solid ${color};
        border-radius: 50%;
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: transform 0.15s;
        position: relative;
      `
      el.innerHTML = `<div style="width:10px;height:10px;background:${color};border-radius:50%;"></div>`
      el.title = district.name

      el.addEventListener('mouseenter', () => { el.style.transform = 'scale(1.25)' })
      el.addEventListener('mouseleave', () => { el.style.transform = 'scale(1)' })
      el.addEventListener('click', () => setSelected({ district, score }))

      const marker = new maplibregl.Marker({ element: el }).setLngLat([lng, lat]).addTo(map)
      markersRef.current.push(marker)
    })
  }, [districts, scores])

  const sel = selected
  const riskInfo = sel?.score ? riskLevel(sel.score.risk_score) : null

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" style={{ height: 'calc(100vh - 12rem)' }}>
      {/* Map */}
      <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-medium text-slate-200">Bản đồ Thành phố</h3>
          <div className="flex gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />Good (70+)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" />Moderate (50-70)</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />Poor (&lt;50)</span>
          </div>
        </div>
        <div ref={mapContainerRef} className="flex-1 w-full" />
      </div>

      {/* Detail Panel */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex flex-col overflow-y-auto custom-scrollbar">
        <h3 className="text-lg font-medium text-slate-200 mb-6 border-b border-slate-700 pb-4 flex items-center justify-between">
          <span>Chi tiết Khu vực</span>
          {sel && <span className="text-blue-400 text-sm">{sel.district.name}</span>}
        </h3>

        {!sel ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-14 h-14 rounded-full bg-slate-700 flex items-center justify-center mb-4">
              <span className="text-2xl">📍</span>
            </div>
            <p className="text-slate-400 text-sm">Nhấn vào một điểm trên bản đồ để xem chi tiết quận/huyện.</p>
          </div>
        ) : (
          <div className="space-y-5 flex-1">
            {riskInfo && (
              <div className={`flex justify-between items-center p-4 rounded-lg border ${riskInfo.bg}`}>
                <span className="text-slate-300 text-sm">Mức độ Rủi ro</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${riskInfo.labelCls} bg-slate-900`}>
                  {riskInfo.label}
                </span>
              </div>
            )}

            {sel.score && (
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'AQI Score', value: Math.round(sel.score.environment_score), cls: 'text-yellow-400' },
                  { label: 'Traffic', value: Math.round(sel.score.traffic_score), cls: 'text-blue-400' },
                  { label: 'Risk', value: Math.round(sel.score.risk_score), cls: 'text-red-400' },
                  { label: 'Overall', value: Math.round(sel.score.overall_score), cls: 'text-emerald-400' },
                ].map(({ label, value, cls }) => (
                  <div key={label} className="bg-slate-900 rounded-lg p-3">
                    <p className="text-slate-400 text-xs mb-1">{label}</p>
                    <p className={`text-xl font-bold ${cls}`}>{value}<span className="text-slate-600 text-xs">/100</span></p>
                    <div className="mt-2 h-1 bg-slate-700 rounded-full">
                      <div className={`h-1 rounded-full ${cls.replace('text-', 'bg-')}`} style={{ width: `${value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t border-slate-700 pt-4 space-y-2">
              <h4 className="text-sm font-medium text-slate-300 mb-3">Hành động Khuyến nghị</h4>
              <button className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                Điều phối Lực lượng
              </button>
              <button className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm font-medium transition-colors border border-slate-600">
                Phát Thông báo Khẩn
              </button>
            </div>
          </div>
        )}

        {/* District list */}
        <div className="mt-6 border-t border-slate-700 pt-4">
          <h4 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Tất cả Quận/Huyện</h4>
          <div className="space-y-1">
            {districts.map(d => {
              const sc = scores.find(s => s.district_id === d.id)
              const isActive = sel?.district.id === d.id
              return (
                <button
                  key={d.id}
                  onClick={() => setSelected({ district: d, score: sc })}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive ? 'bg-blue-600/20 text-blue-300' : 'hover:bg-slate-700/50 text-slate-300'
                  }`}
                >
                  <span>{d.name}</span>
                  {sc && (
                    <span style={{ color: scoreColor(sc.overall_score) }} className="font-bold text-xs">
                      {Math.round(sc.overall_score)}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
