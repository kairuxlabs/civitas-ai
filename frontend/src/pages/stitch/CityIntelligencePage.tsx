import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Building2, Info, Loader2, TrendingDown, TrendingUp, Wind } from 'lucide-react'
import { api } from '../../services/api'
import { useTranslation } from '../../i18n/useTranslation'

export default function CityIntelligencePage() {
  const { t } = useTranslation()
  const [selectedDistrictId, setSelectedDistrictId] = useState(1)

  const categoryMeta = [
    { key: 'traffic_score', label: t('cityIntelligence.traffic'), border: 'border-l-primary', icon: 'text-primary', invert: false },
    { key: 'environment_score', label: t('cityIntelligence.environment'), border: 'border-l-secondary', icon: 'text-secondary', invert: false },
    { key: 'citizen_score', label: t('cityIntelligence.citizen'), border: 'border-l-tertiary', icon: 'text-tertiary', invert: false },
    { key: 'risk_score', label: t('cityIntelligence.risk'), border: 'border-l-error', icon: 'text-error', invert: true },
  ] as const

  const { data: districts } = useQuery({ queryKey: ['districts'], queryFn: api.getDistricts })
  const { data: scores, isLoading, isError } = useQuery({ queryKey: ['scores'], queryFn: api.getScores, refetchInterval: 15000 })
  const { data: aqiHistory } = useQuery({
    queryKey: ['aqi-history', selectedDistrictId],
    queryFn: () => api.getAQIHistory(selectedDistrictId, 12),
  })

  const selectedScore = useMemo(
    () => scores?.find(s => s.district_id === selectedDistrictId) ?? null,
    [scores, selectedDistrictId],
  )
  const selectedDistrict = useMemo(
    () => districts?.find(d => d.id === selectedDistrictId) ?? null,
    [districts, selectedDistrictId],
  )
  const latestAqi = aqiHistory && aqiHistory.length > 0 ? aqiHistory[aqiHistory.length - 1] : null

  if (isLoading) {
    return (
      <div data-testid="city-intelligence-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="city-intelligence-loading" className="flex items-center justify-center py-24">
          <Loader2 size={28} className="animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div data-testid="city-intelligence-page" className="p-margin-desktop space-y-gutter pb-16">
        <div data-testid="city-intelligence-error" className="glass-panel rounded-xl p-6 text-error text-sm">
          {t('common.loadError')}
        </div>
      </div>
    )
  }

  return (
    <div data-testid="city-intelligence-page" className="p-margin-desktop space-y-gutter pb-16">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Building2 size={22} className="text-primary" /> {t('cityIntelligence.title')}
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">{t('cityIntelligence.subtitle')}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(districts ?? []).map(d => (
            <button
              key={d.id}
              type="button"
              data-testid="city-intelligence-district-option"
              onClick={() => setSelectedDistrictId(d.id)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                d.id === selectedDistrictId
                  ? 'bg-primary/20 border-primary text-primary font-semibold'
                  : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-high'
              }`}
            >
              {d.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
        <section className="lg:col-span-5 glass-panel rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xs uppercase tracking-wide text-on-surface-variant">{t('cityIntelligence.overallCityScore')}</h2>
              <p className="text-xs text-secondary mt-1">{selectedDistrict?.name ?? t('cityIntelligence.hanoiMetroArea')}</p>
            </div>
            <Info size={16} className="text-outline" />
          </div>
          <div className="mt-6 flex items-end gap-3">
            <span data-testid="city-intelligence-overall-score" className="text-6xl font-black text-primary tracking-tighter">
              {selectedScore ? Math.round(selectedScore.overall_score) : '—'}
            </span>
            <span className="text-sm font-bold text-outline pb-2">/100</span>
          </div>
          <div className="w-full bg-outline-variant h-1 rounded-full mt-6 overflow-hidden">
            <div
              className="bg-primary h-full rounded-full"
              style={{ width: `${selectedScore ? Math.round(selectedScore.overall_score) : 0}%` }}
            />
          </div>
        </section>

        <section className="lg:col-span-7 glass-panel rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Wind size={16} className="text-secondary" />
            <h2 className="text-sm font-semibold">{t('cityIntelligence.airQuality')}</h2>
          </div>
          {latestAqi ? (
            <div className="flex gap-6">
              <div>
                <p className="text-xs text-on-surface-variant">{t('cityIntelligence.aqiIndex')}</p>
                <p className="text-2xl font-semibold">{Math.round(latestAqi.aqi_index)}</p>
              </div>
              <div>
                <p className="text-xs text-on-surface-variant">{t('cityIntelligence.pm25')}</p>
                <p className="text-2xl font-semibold">{Math.round(latestAqi.pm25)}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-on-surface-variant italic">{t('cityIntelligence.noAqiHistory')}</p>
          )}
        </section>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        {categoryMeta.map(cat => {
          const value = selectedScore ? Math.round(selectedScore[cat.key]) : null
          const good = cat.invert ? (value ?? 0) < 40 : (value ?? 0) >= 60
          return (
            <div key={cat.key} className={`glass-panel rounded-xl p-5 border-l-4 ${cat.border}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">{cat.label}</h3>
                {good ? <TrendingUp size={14} className={cat.icon} /> : <TrendingDown size={14} className="text-error" />}
              </div>
              <span className="text-3xl font-black">
                {value ?? '—'}<span className="text-xs font-normal text-outline ml-1">/100</span>
              </span>
            </div>
          )
        })}
      </section>
    </div>
  )
}
