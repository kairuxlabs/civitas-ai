import { useQuery } from '@tanstack/react-query'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { Shield, Clock, Activity, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import type { CityScore, District, AgentDecisionOut } from '../types'

function riskLabel(score: number): { label: string; color: string; bg: string } {
  if (score >= 60) return { label: 'HIGH', color: 'text-red-400', bg: 'bg-red-950 border-red-800' }
  if (score >= 30) return { label: 'MEDIUM', color: 'text-yellow-400', bg: 'bg-yellow-950 border-yellow-800' }
  return { label: 'LOW', color: 'text-emerald-400', bg: 'bg-emerald-950 border-emerald-800' }
}

function buildRadarData(scores: CityScore[]) {
  if (!scores.length) return [
    { subject: 'Air Quality', value: 50, fullMark: 100 },
    { subject: 'Flooding', value: 40, fullMark: 100 },
    { subject: 'Traffic', value: 45, fullMark: 100 },
    { subject: 'Power Grid', value: 20, fullMark: 100 },
    { subject: 'Public Safety', value: 30, fullMark: 100 },
  ]

  const avg = (fn: (s: CityScore) => number) =>
    Math.round(scores.reduce((a, s) => a + fn(s), 0) / scores.length)

  return [
    { subject: 'Air Quality', value: Math.round(100 - avg(s => s.environment_score)), fullMark: 100 },
    { subject: 'Flooding', value: avg(s => s.risk_score), fullMark: 100 },
    { subject: 'Traffic', value: Math.round(100 - avg(s => s.traffic_score)), fullMark: 100 },
    { subject: 'Power Grid', value: Math.round(avg(s => s.risk_score) * 0.4), fullMark: 100 },
    { subject: 'Public Safety', value: Math.round(100 - avg(s => s.citizen_score)), fullMark: 100 },
  ]
}

function buildTopRecommendation(scores: CityScore[], districts: District[]): string {
  if (!scores.length) return 'Đang tải dữ liệu phân tích...'
  const worst = [...scores].sort((a, b) => b.risk_score - a.risk_score)[0]
  const name = districts.find(d => d.id === worst.district_id)?.name ?? `District ${worst.district_id}`
  const risk = Math.round(worst.risk_score)
  const env = Math.round(worst.environment_score)

  if (risk >= 60) {
    return `Khu vực ${name} đang có nguy cơ rất cao (risk ${risk}/100). Khuyến nghị: kích hoạt hệ thống bơm thoát nước, triển khai lực lượng ứng phó, và phát cảnh báo mức 2 đến cư dân vùng trũng.`
  }
  if (env < 50) {
    return `Chất lượng không khí tại ${name} đang ở mức nguy hiểm (AQI score ${env}/100). Khuyến nghị: hạn chế hoạt động ngoài trời và tăng tần suất xe buýt công cộng.`
  }
  return `Các chỉ số thành phố đang ổn định. Khu vực rủi ro nhất hiện tại là ${name} với điểm risk ${risk}/100. Duy trì giám sát liên tục và cập nhật mỗi 15 phút.`
}

function TimelineItem({ event, isLast }: { event: AgentDecisionOut; isLast: boolean }) {
  const recs = event.recommendations ?? []
  const firstRec = recs[0] ?? 'Phân tích hoàn tất'

  return (
    <div className="flex gap-4 relative">
      {!isLast && <div className="absolute top-6 left-3 w-px h-full bg-slate-700" />}
      <div className="flex flex-col items-center">
        <div className="w-6 h-6 rounded-full border-2 flex items-center justify-center z-10 bg-slate-900 border-blue-500 text-blue-500">
          <Activity size={12} />
        </div>
      </div>
      <div className="pb-6 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-slate-200 truncate max-w-[200px]">{event.query ?? 'Agent Decision'}</span>
          <span className="text-xs text-slate-500 shrink-0">
            {event.created_at ? new Date(event.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : ''}
          </span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed">{firstRec}</p>
        {typeof event.confidence === 'number' && (
          <span className="inline-block mt-1 text-xs text-blue-400">Confidence: {Math.round(event.confidence)}%</span>
        )}
      </div>
    </div>
  )
}

export default function RiskRadarPage() {
  const { data: districts = [] } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores = [], isLoading } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 30000 })
  const { data: timeline = [] } = useQuery({ queryKey: ['timeline'], queryFn: () => api.getTimeline(5) })

  const radarData = buildRadarData(scores)
  const topRec = buildTopRecommendation(scores, districts)
  const ranked = [...scores].sort((a, b) => b.risk_score - a.risk_score)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Radar Chart */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex flex-col items-center">
        <h3 className="text-xl font-medium text-slate-200 mb-6 w-full text-left">City Risk Profile</h3>
        <div className="w-full max-w-md" style={{ aspectRatio: '1' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
              <Radar name="Risk Level" dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: 8, color: '#f8fafc' }}
                formatter={(v) => [`${v}/100`, 'Risk']}
              />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-slate-400 text-sm mt-4 text-center max-w-sm">
          Mức độ rủi ro trên các lĩnh vực hạ tầng thành phố. Giá trị cao = rủi ro cao hơn.
        </p>

        {/* District risk ranking */}
        <div className="w-full mt-6 space-y-2">
          <h4 className="text-sm font-medium text-slate-300 mb-3">District Risk Ranking</h4>
          {isLoading
            ? [1,2,3].map(i => <div key={i} className="h-10 bg-slate-700 rounded-lg animate-pulse" />)
            : ranked.slice(0, 5).map((s, i) => {
                const risk = riskLabel(s.risk_score)
                const name = districts.find(d => d.id === s.district_id)?.name ?? `District ${s.district_id}`
                return (
                  <div key={s.id} className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border ${risk.bg}`}>
                    <span className="text-slate-500 text-xs w-4">{i + 1}</span>
                    <span className="flex-1 text-sm text-slate-200 font-medium">{name}</span>
                    <span className={`text-xs font-bold ${risk.color}`}>{risk.label}</span>
                    <span className={`text-sm font-bold ${risk.color}`}>{Math.round(s.risk_score)}</span>
                  </div>
                )
              })
          }
        </div>
      </div>

      {/* Right column */}
      <div className="space-y-6">
        {/* AI Recommendation */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Risk Mitigation Copilot</h3>
          <div className="bg-slate-900 rounded-lg p-4 border border-blue-500/30">
            <div className="flex gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                <Shield size={16} className="text-white" />
              </div>
              <div>
                <p className="text-sm text-blue-200 font-medium">Civitas AI Recommendation</p>
                <p className="text-slate-300 mt-1 text-sm leading-relaxed">{topRec}</p>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button className="px-3 py-1.5 text-sm rounded bg-slate-700 text-slate-200 hover:bg-slate-600 transition-colors">
                Bỏ qua
              </button>
              <button className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors">
                Thực thi Lệnh
              </button>
            </div>
          </div>
        </div>

        {/* Action Timeline */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex-1">
          <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-400" /> Action Timeline
          </h3>
          {timeline.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-slate-500 text-sm">Chưa có quyết định nào được ghi lại.</p>
              <p className="text-slate-600 text-xs mt-1">Sử dụng AI Copilot để bắt đầu.</p>
            </div>
          ) : (
            <div className="mt-2">
              {timeline.map((event, idx) => (
                <TimelineItem key={event.id} event={event} isLast={idx === timeline.length - 1} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
