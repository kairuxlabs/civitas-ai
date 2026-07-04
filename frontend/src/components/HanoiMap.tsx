import { useState } from 'react'
import type { CityScore } from '../types'

interface DistrictNode {
  id: number
  name: string
  cx: number
  cy: number
  r: number
}

// Approximate positions on a 500×400 canvas representing Hanoi
const DISTRICT_NODES: DistrictNode[] = [
  { id: 1,  name: 'Hoàn Kiếm',   cx: 250, cy: 190, r: 26 },
  { id: 2,  name: 'Ba Đình',      cx: 210, cy: 155, r: 28 },
  { id: 3,  name: 'Đống Đa',      cx: 230, cy: 230, r: 30 },
  { id: 4,  name: 'Hai Bà Trưng', cx: 285, cy: 220, r: 28 },
  { id: 5,  name: 'Hoàng Mai',    cx: 300, cy: 270, r: 32 },
  { id: 6,  name: 'Thanh Xuân',   cx: 230, cy: 275, r: 28 },
  { id: 7,  name: 'Cầu Giấy',     cx: 175, cy: 200, r: 28 },
  { id: 8,  name: 'Long Biên',    cx: 340, cy: 165, r: 30 },
  { id: 9,  name: 'Nam Từ Liêm',  cx: 150, cy: 260, r: 30 },
  { id: 10, name: 'Bắc Từ Liêm',  cx: 165, cy: 130, r: 30 },
  { id: 11, name: 'Tây Hồ',       cx: 220, cy: 110, r: 26 },
  { id: 12, name: 'Hà Đông',      cx: 165, cy: 320, r: 32 },
]

function scoreToColor(score: number | undefined): string {
  if (!score) return '#334155'
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  return '#ef4444'
}

function riskToGlow(riskScore: number | undefined): string {
  if (!riskScore) return 'none'
  if (riskScore >= 60) return 'drop-shadow(0 0 8px #ef4444)'
  if (riskScore >= 30) return 'drop-shadow(0 0 6px #eab308)'
  return 'none'
}

interface Props {
  scores: CityScore[]
  selectedDistrictId: number | null
  onSelectDistrict: (id: number) => void
}

export default function HanoiMap({ scores, selectedDistrictId, onSelectDistrict }: Props) {
  const scoreMap = new Map(scores.map(s => [s.district_id, s]))
  const [hovered, setHovered] = useState<number | null>(null)

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
      {/* Background grid */}
      <svg className="absolute inset-0 w-full h-full opacity-10" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#94a3b8" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Main map SVG */}
      <svg
        viewBox="0 0 500 420"
        className="w-full h-full max-w-2xl"
        style={{ maxHeight: '100%' }}
      >
        {/* City label */}
        <text x="250" y="24" textAnchor="middle" fill="#94a3b8" fontSize="13" fontFamily="sans-serif" letterSpacing="3">
          HANOI • DIGITAL TWIN
        </text>

        {/* Connection lines between districts */}
        {[
          [1,2],[1,3],[1,4],[2,7],[2,11],[3,6],[3,4],[4,5],[5,12],[6,9],[7,9],[7,10],[8,4],[10,11],[12,9]
        ].map(([a, b], i) => {
          const da = DISTRICT_NODES.find(d => d.id === a)!
          const db = DISTRICT_NODES.find(d => d.id === b)!
          return (
            <line
              key={i}
              x1={da.cx} y1={da.cy}
              x2={db.cx} y2={db.cy}
              stroke="#1e3a5f"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              opacity="0.6"
            />
          )
        })}

        {/* District nodes */}
        {DISTRICT_NODES.map(node => {
          const score = scoreMap.get(node.id)
          const isSelected = selectedDistrictId === node.id
          const isHovered = hovered === node.id
          const fill = scoreToColor(score?.overall_score)
          const glow = riskToGlow(score?.risk_score)

          return (
            <g
              key={node.id}
              data-testid={`district-${node.id}`}
              style={{ cursor: 'pointer', filter: glow }}
              onClick={() => onSelectDistrict(node.id)}
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
            >
              {/* Outer ring for selected */}
              {isSelected && (
                <circle
                  cx={node.cx} cy={node.cy}
                  r={node.r + 8}
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="2"
                  opacity="0.8"
                >
                  <animate attributeName="r" values={`${node.r + 6};${node.r + 12};${node.r + 6}`} dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.8;0.3;0.8" dur="2s" repeatCount="indefinite" />
                </circle>
              )}

              {/* Pulse ring for hover */}
              {isHovered && !isSelected && (
                <circle
                  cx={node.cx} cy={node.cy}
                  r={node.r + 6}
                  fill="none"
                  stroke={fill}
                  strokeWidth="1.5"
                  opacity="0.5"
                />
              )}

              {/* Main district circle */}
              <circle
                cx={node.cx} cy={node.cy}
                r={node.r}
                fill={fill}
                fillOpacity={isHovered || isSelected ? 0.9 : 0.6}
                stroke={isSelected ? '#3b82f6' : fill}
                strokeWidth={isSelected ? 2.5 : 1.5}
              />

              {/* Score text */}
              {score && (
                <text
                  x={node.cx} y={node.cy + 1}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="white"
                  fontSize="10"
                  fontWeight="700"
                  fontFamily="monospace"
                >
                  {Math.round(score.overall_score)}
                </text>
              )}

              {/* District name */}
              <text
                x={node.cx} y={node.cy + node.r + 12}
                textAnchor="middle"
                fill={isSelected ? '#93c5fd' : '#94a3b8'}
                fontSize="9"
                fontFamily="sans-serif"
                fontWeight={isSelected ? '700' : '400'}
              >
                {node.name}
              </text>
            </g>
          )
        })}

        {/* Legend */}
        <g transform="translate(10, 380)">
          {[
            { color: '#22c55e', label: 'Good (≥80)' },
            { color: '#eab308', label: 'Fair (60–80)' },
            { color: '#ef4444', label: 'Poor (<60)' },
          ].map(({ color, label }, i) => (
            <g key={i} transform={`translate(${i * 120}, 0)`}>
              <circle cx="6" cy="6" r="5" fill={color} fillOpacity="0.7" />
              <text x="16" y="10" fill="#64748b" fontSize="9" fontFamily="sans-serif">{label}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  )
}
