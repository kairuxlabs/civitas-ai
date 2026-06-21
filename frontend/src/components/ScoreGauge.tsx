// frontend/src/components/ScoreGauge.tsx
interface Props {
  score: number;
  label: string;
  size?: 'sm' | 'lg';
}

export default function ScoreGauge({ score, label, size = 'sm' }: Props) {
  const color = score >= 70 ? 'text-emerald-400' : score >= 50 ? 'text-yellow-400' : 'text-red-400'
  const ring = score >= 70 ? 'stroke-emerald-400' : score >= 50 ? 'stroke-yellow-400' : 'stroke-red-400'
  const r = size === 'lg' ? 54 : 36
  const circumference = 2 * Math.PI * r
  const dash = (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`relative ${size === 'lg' ? 'w-32 h-32' : 'w-20 h-20'}`}>
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
          <circle
            cx="60" cy="60" r={r} fill="none"
            className={ring} strokeWidth="8"
            strokeDasharray={`${dash} ${circumference}`}
            strokeLinecap="round"
          />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center font-bold ${color} ${size === 'lg' ? 'text-2xl' : 'text-lg'}`}>
          {Math.round(score)}
        </span>
      </div>
      <span className="text-slate-400 text-xs uppercase tracking-wider">{label}</span>
    </div>
  )
}
