import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, Brain, CheckCircle, ChevronRight, Loader2, Rocket, ShieldAlert, XCircle,
} from 'lucide-react'
import { api } from '../services/api'
import SimulationPanel from '../components/SimulationPanel'
import type { RuntimeRun, RuntimeTask } from '../types'

// ─── Presets ──────────────────────────────────────────────────────────────────
const GOAL_PRESETS = [
  'Chuẩn bị thành phố cho trận mưa lớn tối nay',
  'Ứng phó ô nhiễm không khí nghiêm trọng ngày mai',
  'Đảm bảo an toàn cho lễ hội cuối tuần tại Hoàn Kiếm',
]

const RUN_STATUS_LABEL: Record<string, string> = {
  planning: 'Đang lập kế hoạch',
  running: 'Đang thực thi',
  reflecting: 'Đang tự đánh giá',
  deciding: 'Đang ra quyết định',
  awaiting_approval: 'Chờ phê duyệt',
  executing_workflow: 'Đang chạy workflow',
  done: 'Hoàn tất',
  failed: 'Thất bại',
  rejected: 'Đã từ chối',
}

const ACTIVE_STATUSES = new Set(['planning', 'running', 'reflecting', 'deciding', 'executing_workflow'])

// ─── DAG layout: group tasks into columns by dependency depth ─────────────────
function taskDepth(task: RuntimeTask, byId: Map<string, RuntimeTask>, seen: Set<string> = new Set()): number {
  if (task.depends_on.length === 0 || seen.has(task.id)) return 0
  seen.add(task.id)
  const parents = task.depends_on.map(d => byId.get(d)).filter((t): t is RuntimeTask => !!t)
  if (parents.length === 0) return 0
  return 1 + Math.max(...parents.map(p => taskDepth(p, byId, seen)))
}

const NODE_COLORS: Record<string, string> = {
  pending: 'fill-slate-800 stroke-slate-600',
  running: 'fill-blue-900 stroke-blue-400',
  done: 'fill-emerald-900 stroke-emerald-500',
  failed: 'fill-rose-900 stroke-rose-500',
}

function RuntimeDag({ tasks }: { tasks: RuntimeTask[] }) {
  const byId = useMemo(() => new Map(tasks.map(t => [t.id, t])), [tasks])
  const columns = useMemo(() => {
    const cols: RuntimeTask[][] = []
    for (const t of tasks) {
      const d = taskDepth(t, byId)
      ;(cols[d] ||= []).push(t)
    }
    return cols
  }, [tasks, byId])

  if (tasks.length === 0) {
    return <div className="text-slate-600 text-sm italic p-6 text-center">Chưa có kế hoạch — hãy giao một mục tiêu</div>
  }

  const colW = 150
  const rowH = 52
  const width = Math.max(columns.length * colW, 300)
  const height = Math.max(...columns.map(c => c.length)) * rowH + 20

  const pos = new Map<string, { x: number; y: number }>()
  columns.forEach((col, ci) =>
    col.forEach((t, ri) => pos.set(t.id, { x: ci * colW + 70, y: ri * rowH + 32 })),
  )

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
      {tasks.flatMap(t =>
        t.depends_on.map(dep => {
          const from = pos.get(dep)
          const to = pos.get(t.id)
          if (!from || !to) return null
          return (
            <path
              key={`${dep}->${t.id}`}
              d={`M ${from.x + 56} ${from.y} C ${from.x + 90} ${from.y}, ${to.x - 90} ${to.y}, ${to.x - 56} ${to.y}`}
              className="stroke-slate-600 fill-none"
              strokeWidth={1.5}
              markerEnd="url(#arrow)"
            />
          )
        }),
      )}
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6" className="fill-none stroke-slate-500" />
        </marker>
      </defs>
      {tasks.map(t => {
        const p = pos.get(t.id)!
        return (
          <g key={t.id}>
            <rect
              x={p.x - 56} y={p.y - 16} width={112} height={32} rx={8}
              strokeWidth={1.5}
              className={`${NODE_COLORS[t.status]} ${t.status === 'running' ? 'animate-pulse' : ''}`}
            />
            <text x={p.x} y={p.y - 2} textAnchor="middle" className="fill-slate-200 text-[11px] font-semibold">
              {t.agent}
            </text>
            <text x={p.x} y={p.y + 10} textAnchor="middle" className="fill-slate-500 text-[9px]">
              {t.status}{t.latency_ms != null ? ` · ${Math.round(t.latency_ms)}ms` : ''}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

// ─── Decision card ────────────────────────────────────────────────────────────
const RISK_STYLES: Record<string, string> = {
  high: 'bg-rose-950 text-rose-300 border-rose-700',
  medium: 'bg-amber-950 text-amber-300 border-amber-700',
  low: 'bg-emerald-950 text-emerald-300 border-emerald-700',
}

function DecisionCard({ run, onResolve, resolving }: {
  run: RuntimeRun
  onResolve: (approved: boolean) => void
  resolving: boolean
}) {
  const d = run.decision
  if (!d) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Brain size={16} className="text-purple-400" /> Quyết định của Runtime
        </h3>
        <span className={`text-xs px-2 py-0.5 rounded border ${RISK_STYLES[d.risk] ?? RISK_STYLES.low}`}>
          Rủi ro: {d.risk}
        </span>
      </div>
      <p className="text-sm text-slate-300">{d.summary}</p>
      <p className="text-xs text-slate-400"><span className="text-slate-500">Dự báo:</span> {d.prediction}</p>
      <ul className="space-y-1">
        {d.recommendation.map((r, i) => (
          <li key={i} className="text-xs text-slate-300 flex gap-1.5">
            <ChevronRight size={13} className="text-cyan-500 shrink-0 mt-0.5" /> {r}
          </li>
        ))}
      </ul>
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-slate-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${d.confidence >= 75 ? 'bg-emerald-500' : d.confidence >= 55 ? 'bg-amber-500' : 'bg-rose-500'}`}
            style={{ width: `${d.confidence}%` }}
          />
        </div>
        <span className="text-xs text-slate-400 tabular-nums">{Math.round(d.confidence)}%</span>
      </div>
      {(d.evidence ?? []).length > 0 && (
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-300">Bằng chứng ({(d.evidence ?? []).length})</summary>
          <ul className="mt-1 space-y-0.5 pl-3">
            {(d.evidence ?? []).map((e, i) => (
              <li key={i}>
                <span className="text-slate-400">{e.agent}</span>
                {e.source && <span className="text-slate-600"> ({e.source})</span>}: {e.content ?? e.summary}
              </li>
            ))}
          </ul>
        </details>
      )}
      {run.status === 'awaiting_approval' && (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => onResolve(true)}
            disabled={resolving}
            className="flex-1 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-semibold py-2 rounded flex items-center justify-center gap-1.5"
          >
            <CheckCircle size={14} /> Phê duyệt
          </button>
          <button
            onClick={() => onResolve(false)}
            disabled={resolving}
            className="flex-1 bg-rose-800 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-semibold py-2 rounded flex items-center justify-center gap-1.5"
          >
            <XCircle size={14} /> Từ chối
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function MissionControlPage() {
  const [goal, setGoal] = useState('')
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: run } = useQuery({
    queryKey: ['v2-run', activeRunId],
    queryFn: () => api.getRun(activeRunId!),
    enabled: !!activeRunId,
    refetchInterval: q => {
      const status = q.state.data?.status
      return status && ACTIVE_STATUSES.has(status) ? 1200 : status === 'awaiting_approval' ? 4000 : false
    },
  })

  const { data: runs } = useQuery({
    queryKey: ['v2-runs'],
    queryFn: api.getRuns,
    refetchInterval: 5000,
  })

  const { data: monitor } = useQuery({
    queryKey: ['v2-monitor'],
    queryFn: api.getRuntimeMonitor,
    refetchInterval: 5000,
  })

  const submit = useMutation({
    mutationFn: (g: string) => api.submitGoal(g),
    onSuccess: r => {
      setActiveRunId(r.run_id)
      queryClient.invalidateQueries({ queryKey: ['v2-runs'] })
    },
  })

  const resolve = useMutation({
    mutationFn: (approved: boolean) => api.resolveRun(activeRunId!, approved),
    onSuccess: r => queryClient.setQueryData(['v2-run', activeRunId], r),
  })

  const isActive = run && ACTIVE_STATUSES.has(run.status)

  return (
    <div className="h-full bg-slate-950 text-slate-100 overflow-y-auto custom-scrollbar">
      <div className="max-w-7xl mx-auto p-4 space-y-4">
        {/* Goal input */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
          <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Rocket size={16} className="text-cyan-400" /> Giao mục tiêu cho CityOS Runtime
          </h2>
          <div className="flex gap-2">
            <input
              value={goal}
              onChange={e => setGoal(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && goal.trim().length >= 3 && submit.mutate(goal.trim())}
              placeholder="Ví dụ: Chuẩn bị thành phố cho trận mưa lớn tối nay…"
              className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm placeholder:text-slate-600 focus:outline-none focus:border-cyan-600"
            />
            <button
              onClick={() => submit.mutate(goal.trim())}
              disabled={goal.trim().length < 3 || submit.isPending}
              className="bg-cyan-700 hover:bg-cyan-600 disabled:opacity-40 text-white text-sm font-semibold px-4 rounded flex items-center gap-2"
            >
              {submit.isPending ? <Loader2 size={15} className="animate-spin" /> : <Rocket size={15} />}
              Thực thi
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {GOAL_PRESETS.map(p => (
              <button
                key={p}
                onClick={() => { setGoal(p); submit.mutate(p) }}
                className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-full"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Digital Twin simulation + crawling */}
        <SimulationPanel />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* DAG + monitor */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Activity size={16} className="text-blue-400" /> Runtime Graph
                </h3>
                {run && (
                  <span className="text-xs text-slate-400 flex items-center gap-1.5">
                    {isActive && <Loader2 size={12} className="animate-spin text-blue-400" />}
                    {RUN_STATUS_LABEL[run.status] ?? run.status}
                  </span>
                )}
              </div>
              <RuntimeDag tasks={run?.tasks ?? []} />
            </div>

            {/* Agent monitor */}
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-bold text-slate-200 mb-2">Agent Monitor</h3>
              <div className="flex flex-wrap gap-2">
                {monitor && Object.entries(monitor.agents).length > 0 ? (
                  Object.entries(monitor.agents).map(([name, s]) => (
                    <div key={name} className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-xs">
                      <span className="font-semibold text-slate-200">{name}</span>
                      <span className="text-slate-500 ml-2">
                        {s.runs} lượt · {s.failures} lỗi{s.avg_latency_ms != null ? ` · ${s.avg_latency_ms}ms` : ''}
                      </span>
                    </div>
                  ))
                ) : (
                  <span className="text-xs text-slate-600 italic">Chưa có dữ liệu agent</span>
                )}
              </div>
            </div>

            {/* Timeline */}
            {run && run.timeline.length > 0 && (
              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <h3 className="text-sm font-bold text-slate-200 mb-2">Timeline</h3>
                <ul className="space-y-1 max-h-48 overflow-y-auto custom-scrollbar">
                  {[...run.timeline].reverse().map((t, i) => (
                    <li key={i} className="text-xs text-slate-400 flex gap-2">
                      <span className="text-slate-600 tabular-nums shrink-0">
                        {new Date(t.ts).toLocaleTimeString('vi-VN')}
                      </span>
                      <span className="text-cyan-600 shrink-0">[{t.actor}]</span>
                      <span>{t.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right column: decision + workflow + history */}
          <div className="space-y-4">
            {run?.decision && (
              <DecisionCard run={run} onResolve={a => resolve.mutate(a)} resolving={resolve.isPending} />
            )}

            {run && run.workflow_steps.length > 0 && (
              <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                <h3 className="text-sm font-bold text-slate-200 mb-2 flex items-center gap-2">
                  <ShieldAlert size={15} className="text-emerald-400" /> Workflow
                </h3>
                <ul className="space-y-1.5">
                  {run.workflow_steps.map((s, i) => (
                    <li key={i} className="text-xs text-slate-300 flex gap-2 items-start">
                      <CheckCircle size={13} className="text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold">{s.step}</span>
                        <span className="text-slate-500 ml-1">{s.detail}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-bold text-slate-200 mb-2">Lịch sử Run</h3>
              <ul className="space-y-1 max-h-60 overflow-y-auto custom-scrollbar">
                {(runs ?? []).map(r => (
                  <li key={r.run_id}>
                    <button
                      onClick={() => setActiveRunId(r.run_id)}
                      className={`w-full text-left text-xs rounded px-2 py-1.5 border ${
                        r.run_id === activeRunId
                          ? 'bg-slate-800 border-cyan-700 text-slate-200'
                          : 'border-transparent hover:bg-slate-800 text-slate-400'
                      }`}
                    >
                      <div className="truncate">{r.goal}</div>
                      <div className="text-slate-600">
                        {RUN_STATUS_LABEL[r.status] ?? r.status}
                        {r.confidence != null ? ` · ${Math.round(r.confidence)}%` : ''}
                      </div>
                    </button>
                  </li>
                ))}
                {(runs ?? []).length === 0 && (
                  <li className="text-xs text-slate-600 italic">Chưa có run nào</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
