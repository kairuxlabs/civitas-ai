import type { AgentEvent } from '../types'

const AGENTS = [
  { name: 'Traffic Agent',      x: 70,  y: 110 },
  { name: 'Environment Agent',  x: 170, y: 110 },
  { name: 'Event Agent',        x: 270, y: 110 },
  { name: 'Citizen Agent',      x: 370, y: 110 },
  { name: 'Knowledge Agent',    x: 470, y: 110 },
  { name: 'Decision Agent',     x: 270, y: 220 },
  { name: 'Explanation Agent',  x: 270, y: 310 },
]

const SUPERVISOR = { name: 'Supervisor', x: 270, y: 30 }

const EDGES = [
  [SUPERVISOR, AGENTS[0]],
  [SUPERVISOR, AGENTS[1]],
  [SUPERVISOR, AGENTS[2]],
  [SUPERVISOR, AGENTS[3]],
  [SUPERVISOR, AGENTS[4]],
  [AGENTS[0], AGENTS[5]],
  [AGENTS[1], AGENTS[5]],
  [AGENTS[2], AGENTS[5]],
  [AGENTS[3], AGENTS[5]],
  [AGENTS[4], AGENTS[5]],
  [AGENTS[5], AGENTS[6]],
]

function statusColor(status: string): { fill: string; stroke: string; glow: string } {
  switch (status) {
    case 'running': return { fill: '#1d4ed8', stroke: '#3b82f6', glow: '0 0 14px 4px #3b82f6' }
    case 'done':    return { fill: '#14532d', stroke: '#22c55e', glow: '0 0 10px 3px #22c55e' }
    case 'waiting': return { fill: '#78350f', stroke: '#f59e0b', glow: '0 0 10px 3px #f59e0b' }
    default:        return { fill: '#1e293b', stroke: '#475569', glow: 'none' }
  }
}

function supervisorColor(status: string) {
  switch (status) {
    case 'planning': return { fill: '#312e81', stroke: '#818cf8', glow: '0 0 16px 5px #818cf8' }
    case 'done':     return { fill: '#14532d', stroke: '#22c55e', glow: '0 0 12px 4px #22c55e' }
    default:         return { fill: '#1e293b', stroke: '#475569', glow: 'none' }
  }
}

interface Props {
  events: AgentEvent[]
}

export default function AgentGraph({ events }: Props) {
  const agentStatus = new Map<string, string>()

  for (const e of events) {
    if (e.type === 'pipeline_start') agentStatus.set('Supervisor', 'planning')
    else if (e.type === 'pipeline_done') agentStatus.set('Supervisor', 'done')
    else if (e.type === 'agent_update') agentStatus.set(e.agent, e.status)
  }

  const supStyle = supervisorColor(agentStatus.get('Supervisor') ?? 'idle')

  return (
    <div className="w-full h-full bg-slate-950 rounded-xl border border-slate-800 overflow-hidden p-1">
      <svg viewBox="0 0 540 360" className="w-full h-full">
        {/* Edges */}
        {EDGES.map(([from, to], i) => (
          <line
            key={i}
            x1={from.x} y1={from.y}
            x2={to.x}   y2={to.y}
            stroke="#334155"
            strokeWidth="1.5"
            strokeDasharray="5 4"
          />
        ))}

        {/* Supervisor node */}
        <g>
          <circle
            cx={SUPERVISOR.x} cy={SUPERVISOR.y}
            r="22"
            fill={supStyle.fill}
            stroke={supStyle.stroke}
            strokeWidth="2"
            style={{ filter: agentStatus.get('Supervisor') ? `drop-shadow(${supStyle.glow})` : 'none' }}
          />
          {agentStatus.get('Supervisor') === 'planning' && (
            <circle
              cx={SUPERVISOR.x} cy={SUPERVISOR.y}
              r="22"
              fill="none"
              stroke="#818cf8"
              strokeWidth="2"
              opacity="0"
            >
              <animate attributeName="r" values="22;34;22" dur="1.5s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0;0.8" dur="1.5s" repeatCount="indefinite" />
            </circle>
          )}
          <text x={SUPERVISOR.x} y={SUPERVISOR.y + 1} textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="8" fontWeight="700">SUP</text>
          <text x={SUPERVISOR.x} y={SUPERVISOR.y + 33} textAnchor="middle" fill="#94a3b8" fontSize="8">Supervisor</text>
        </g>

        {/* Agent nodes */}
        {AGENTS.map(agent => {
          const status = agentStatus.get(agent.name) ?? 'idle'
          const { fill, stroke, glow } = statusColor(status)
          const shortName = agent.name.split(' ')[0]
          return (
            <g key={agent.name}>
              {status === 'running' && (
                <circle cx={agent.x} cy={agent.y} r="18" fill="none" stroke="#3b82f6" strokeWidth="1.5" opacity="0">
                  <animate attributeName="r" values="18;30;18" dur="1.2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.8;0;0.8" dur="1.2s" repeatCount="indefinite" />
                </circle>
              )}
              <circle
                cx={agent.x} cy={agent.y}
                r="18"
                fill={fill}
                stroke={stroke}
                strokeWidth="1.8"
                style={{ filter: status !== 'idle' ? `drop-shadow(${glow})` : 'none' }}
              />
              <text x={agent.x} y={agent.y + 1} textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="7" fontWeight="600">
                {shortName.slice(0, 4).toUpperCase()}
              </text>
              <text x={agent.x} y={agent.y + 28} textAnchor="middle" fill="#94a3b8" fontSize="7.5">
                {agent.name.replace(' Agent', '')}
              </text>
              {status === 'done' && (
                <text x={agent.x + 14} y={agent.y - 14} fill="#22c55e" fontSize="10">✓</text>
              )}
              {status === 'running' && (
                <text x={agent.x + 14} y={agent.y - 14} fill="#3b82f6" fontSize="10">⟳</text>
              )}
            </g>
          )
        })}

        {/* Status label */}
        <text x="270" y="348" textAnchor="middle" fill="#64748b" fontSize="9">
          {agentStatus.size === 0 ? 'Waiting for query...' :
            agentStatus.get('Supervisor') === 'done' ? '✓ Pipeline complete' :
            agentStatus.get('Supervisor') === 'planning' ? '⟳ Pipeline running...' : 'Idle'}
        </text>
      </svg>
    </div>
  )
}
