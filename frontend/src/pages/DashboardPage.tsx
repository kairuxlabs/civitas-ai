import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'
import { Wind, CloudRain, Users, Zap, TrendingUp, AlertTriangle, AlertCircle, Info, Map as MapIcon } from 'lucide-react'
import { api } from '../services/api'
import type { CityScore, District, AQIPoint } from '../types'

function getColor(score: number) {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

function ScoreGauge({ score, title, trend }: { score: number; title: string; trend?: string }) {
  return (
    <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex flex-col items-center justify-center relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <h3 className="text-slate-400 text-sm font-medium mb-2 text-center">{title}</h3>
      <div className="flex items-end gap-1">
        <span className={`text-4xl font-bold tracking-tighter ${getColor(score)}`}>
          {Math.round(score)}
        </span>
        <span className="text-slate-500 text-sm mb-1">/100</span>
      </div>
      {trend && (
        <div className={`mt-2 text-xs flex items-center ${trend.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
          <TrendingUp className="w-3 h-3 mr-1" />{trend}
        </div>
      )}
    </div>
  )
}

function MetricCard({
  icon: Icon, title, value, unit, status = 'normal'
}: {
  icon: React.ElementType; title: string; value: string; unit: string; status?: 'normal' | 'warning' | 'critical'
}) {
  const statusColor = { normal: 'text-blue-400', warning: 'text-yellow-400', critical: 'text-red-400' }[status]
  return (
    <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-slate-900 ${statusColor}`}>
        <Icon size={24} />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{title}</p>
        <p className="text-2xl font-semibold text-slate-100">
          {value} <span className="text-sm text-slate-500 font-normal">{unit}</span>
        </p>
      </div>
    </div>
  )
}

function AlertBanner({ type, message, district, time }: { type: 'warning' | 'critical' | 'info'; message: string; district: string; time: string }) {
  const icons = {
    warning: <AlertTriangle className="text-yellow-500 w-5 h-5 shrink-0" />,
    critical: <AlertCircle className="text-red-500 w-5 h-5 shrink-0" />,
    info: <Info className="text-blue-500 w-5 h-5 shrink-0" />,
  }
  const bgs = {
    warning: 'bg-yellow-500/10 border-yellow-500/20',
    critical: 'bg-red-500/10 border-red-500/20',
    info: 'bg-blue-500/10 border-blue-500/20',
  }
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${bgs[type]}`}>
      {icons[type]}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-200">{message}</p>
        <div className="flex justify-between items-center mt-1">
          <span className="text-xs text-slate-500">{district}</span>
          <span className="text-xs text-slate-500">{time}</span>
        </div>
      </div>
    </div>
  )
}

function deriveAlerts(scores: CityScore[], districts: District[]) {
  const alerts: { type: 'warning' | 'critical' | 'info'; message: string; district: string; time: string }[] = []
  const name = (id: number) => districts.find(d => d.id === id)?.name ?? `District ${id}`

  scores.forEach(s => {
    if (s.risk_score >= 60) {
      alerts.push({ type: 'critical', message: `Nguy cơ cao tại ${name(s.district_id)}: risk score ${Math.round(s.risk_score)}`, district: name(s.district_id), time: 'Vừa cập nhật' })
    } else if (s.risk_score >= 30) {
      alerts.push({ type: 'warning', message: `Cảnh báo mức trung bình tại ${name(s.district_id)}: risk ${Math.round(s.risk_score)}`, district: name(s.district_id), time: 'Vừa cập nhật' })
    }
    if (s.environment_score < 50) {
      alerts.push({ type: 'warning', message: `AQI vượt ngưỡng an toàn tại ${name(s.district_id)}`, district: name(s.district_id), time: 'Vừa cập nhật' })
    }
  })

  if (alerts.length === 0) {
    alerts.push({ type: 'info', message: 'Tất cả các chỉ số đang trong ngưỡng bình thường.', district: 'Toàn thành phố', time: 'Vừa cập nhật' })
  }

  return alerts.slice(0, 5)
}

function riskLevel(score: number): { label: string; cls: string } {
  if (score >= 60) return { label: 'HIGH', cls: 'bg-red-500/10 text-red-400' }
  if (score >= 30) return { label: 'MEDIUM', cls: 'bg-yellow-500/10 text-yellow-400' }
  return { label: 'LOW', cls: 'bg-green-500/10 text-green-400' }
}

function AQIFallback(districtId: number): AQIPoint[] {
  const base = 60 + (districtId % 5) * 10
  return ['00:00','04:00','08:00','12:00','16:00','20:00'].map((time, i) => ({
    time,
    aqi_index: Math.round(base + Math.sin(i) * 20),
    pm25: Math.round((base * 0.6 + Math.sin(i) * 12) * 10) / 10,
  }))
}

export default function DashboardPage() {
  const [selectedDistrictId, setSelectedDistrictId] = useState<number>(1)

  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [] } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })
  const { data: aqiHistory = [] } = useQuery({
    queryKey: ['aqi-history', selectedDistrictId],
    queryFn: () => api.getAQIHistory(selectedDistrictId, 24),
    placeholderData: AQIFallback(selectedDistrictId),
  })

  const avg = (fn: (s: CityScore) => number) =>
    scores.length ? Math.round(scores.reduce((a, s) => a + fn(s), 0) / scores.length) : 0

  const overall = avg(s => s.overall_score)
  const metrics = {
    Environment: avg(s => s.environment_score),
    Traffic: avg(s => s.traffic_score),
    Citizen: avg(s => s.citizen_score),
    Safety: avg(s => 100 - s.risk_score),
    Risk: avg(s => s.risk_score),
  }

  const alerts = deriveAlerts(scores, districts)
  const chartData = aqiHistory.length > 0 ? aqiHistory : AQIFallback(selectedDistrictId)

  const avgRain = 12
  const gridLoad = Math.min(99, Math.round(70 + (100 - metrics.Environment) * 0.3))

  return (
    <div className="space-y-6">
      {/* Score gauges */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="col-span-2 md:col-span-3 lg:col-span-1">
          <ScoreGauge score={overall} title="Overall City Score" trend="+2.4%" />
        </div>
        {Object.entries(metrics).map(([key, val]) => (
          <ScoreGauge key={key} score={val} title={key} />
        ))}
      </div>

      {/* AQI Chart + Conditions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
              <Wind className="w-5 h-5 text-blue-400" /> Air Quality Index (AQI) Trend
            </h3>
            <select
              value={selectedDistrictId}
              onChange={e => setSelectedDistrictId(Number(e.target.value))}
              className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-300 focus:outline-none"
            >
              {districts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc', borderRadius: 8 }}
                  itemStyle={{ color: '#60a5fa' }}
                />
                <Line type="monotone" dataKey="aqi_index" name="AQI" stroke="#3b82f6" strokeWidth={3}
                  dot={{ r: 4, fill: '#1e293b', strokeWidth: 2 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium text-slate-200">Current Conditions</h3>
          <MetricCard icon={CloudRain} title="Precipitation" value={String(avgRain)} unit="mm/h" status="warning" />
          <MetricCard icon={Users} title="Active Population" value="1.2" unit="M" />
          <MetricCard icon={Zap} title="Grid Load" value={String(gridLoad)} unit="%" status={gridLoad > 85 ? 'warning' : 'normal'} />
        </div>
      </div>

      {/* District table + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-5">
          <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
            <MapIcon className="w-5 h-5 text-emerald-400" /> District Overview
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400 text-sm">
                  <th className="pb-3 font-medium">District</th>
                  <th className="pb-3 font-medium">Risk Level</th>
                  <th className="pb-3 font-medium">Overall</th>
                  <th className="pb-3 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {scores.map(s => {
                  const district = districts.find(d => d.id === s.district_id)
                  const risk = riskLevel(s.risk_score)
                  return (
                    <tr key={s.id} className="border-b border-slate-700/50 hover:bg-slate-700/20 transition-colors">
                      <td className="py-3 text-slate-200 font-medium">{district?.name ?? `District ${s.district_id}`}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${risk.cls}`}>{risk.label}</span>
                      </td>
                      <td className="py-3 text-slate-300">{Math.round(s.overall_score)}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${s.overall_score >= 75 ? 'bg-green-500' : s.overall_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                              style={{ width: `${s.overall_score}%` }}
                            />
                          </div>
                          <span className="text-sm text-slate-400">{Math.round(s.overall_score)}</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {scores.length === 0 && (
                  <tr><td colSpan={4} className="py-8 text-center text-slate-500">Đang tải dữ liệu...</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 flex flex-col">
          <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" /> Active Alerts
          </h3>
          <div className="flex-1 space-y-2 custom-scrollbar overflow-y-auto">
            {alerts.map((a, i) => <AlertBanner key={i} {...a} />)}
          </div>
          <button className="w-full mt-4 py-2 text-sm text-slate-300 hover:text-white bg-slate-700/50 hover:bg-slate-700 rounded-lg transition-colors border border-slate-600">
            View All Alerts
          </button>
        </div>
      </div>
    </div>
  )
}
