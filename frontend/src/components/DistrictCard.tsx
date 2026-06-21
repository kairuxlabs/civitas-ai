// frontend/src/components/DistrictCard.tsx
import type { CityScore, District } from '../types'
import ScoreGauge from './ScoreGauge'

interface Props {
  district: District;
  score?: CityScore;
  onClick?: () => void;
  selected?: boolean;
}

export default function DistrictCard({ district, score, onClick, selected }: Props) {
  return (
    <div
      onClick={onClick}
      className={`cursor-pointer rounded-xl p-4 border transition-all ${
        selected
          ? 'border-blue-500 bg-slate-800'
          : 'border-slate-700 bg-slate-800/50 hover:border-slate-500'
      }`}
    >
      <h3 className="font-semibold text-slate-200 mb-3">{district.name}</h3>
      {score ? (
        <div className="grid grid-cols-2 gap-2">
          <ScoreGauge score={score.traffic_score} label="Traffic" />
          <ScoreGauge score={score.environment_score} label="Air" />
          <ScoreGauge score={score.citizen_score} label="Citizen" />
          <ScoreGauge score={100 - score.risk_score} label="Safety" />
        </div>
      ) : (
        <p className="text-slate-500 text-sm">No data</p>
      )}
      {score && (
        <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
          <span className="text-slate-400 text-xs">Overall</span>
          <span className={`font-bold text-lg ${
            score.overall_score >= 70 ? 'text-emerald-400' :
            score.overall_score >= 50 ? 'text-yellow-400' : 'text-red-400'
          }`}>{Math.round(score.overall_score)}/100</span>
        </div>
      )}
    </div>
  )
}
