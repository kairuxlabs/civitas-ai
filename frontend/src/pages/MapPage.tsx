// frontend/src/pages/MapPage.tsx
import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { api } from '../services/api'
import type { District, CityScore } from '../types'

export default function MapPage() {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstance = useRef<maplibregl.Map | null>(null)
  const [selectedDistrict, setSelectedDistrict] = useState<{ district: District; score?: CityScore } | null>(null)

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [] } = useQuery({ queryKey: ['scores'], queryFn: api.getScores })

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return
    mapInstance.current = new maplibregl.Map({
      container: mapRef.current,
      style: 'https://tiles.openfreemap.org/styles/dark',
      center: [105.8542, 21.0285],
      zoom: 11,
    })
    mapInstance.current.addControl(new maplibregl.NavigationControl())
  }, [])

  useEffect(() => {
    if (!mapInstance.current || !districts.length) return
    const map = mapInstance.current

    districts.forEach(d => {
      const score = scores.find(s => s.district_id === d.id)
      const color = !score ? '#64748b' :
        score.overall_score >= 70 ? '#10b981' :
        score.overall_score >= 50 ? '#f59e0b' : '#ef4444'

      const marker = new maplibregl.Marker({ color })
        .setLngLat([105.8542 + (Math.random() - 0.5) * 0.15, 21.0285 + (Math.random() - 0.5) * 0.12])
        .addTo(map)

      marker.getElement().addEventListener('click', () => {
        setSelectedDistrict({ district: d, score })
      })
    })
  }, [districts, scores])

  return (
    <div className="relative h-[calc(100vh-8rem)] rounded-xl overflow-hidden border border-slate-800">
      <div ref={mapRef} className="w-full h-full" />

      {selectedDistrict && (
        <div className="absolute top-4 right-4 w-72 bg-slate-900/95 backdrop-blur border border-slate-700 rounded-xl p-4 space-y-3">
          <div className="flex justify-between items-start">
            <h3 className="font-bold text-white">{selectedDistrict.district.name}</h3>
            <button onClick={() => setSelectedDistrict(null)} className="text-slate-500 hover:text-white">✕</button>
          </div>
          {selectedDistrict.score && (
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-slate-800 rounded-lg p-2">
                <p className="text-slate-400 text-xs">AQI Index</p>
                <p className="font-bold text-yellow-400">{Math.round(selectedDistrict.score.environment_score)}</p>
              </div>
              <div className="bg-slate-800 rounded-lg p-2">
                <p className="text-slate-400 text-xs">Traffic</p>
                <p className="font-bold text-blue-400">{Math.round(selectedDistrict.score.traffic_score)}</p>
              </div>
              <div className="bg-slate-800 rounded-lg p-2">
                <p className="text-slate-400 text-xs">Risk</p>
                <p className="font-bold text-red-400">{Math.round(selectedDistrict.score.risk_score)}</p>
              </div>
              <div className="bg-slate-800 rounded-lg p-2">
                <p className="text-slate-400 text-xs">Overall</p>
                <p className="font-bold text-emerald-400">{Math.round(selectedDistrict.score.overall_score)}/100</p>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="absolute bottom-4 left-4 bg-slate-900/80 backdrop-blur rounded-lg px-3 py-2 flex gap-4 text-xs">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"/>Good (70+)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block"/>Moderate (50-70)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block"/>Poor (&lt;50)</span>
      </div>
    </div>
  )
}
