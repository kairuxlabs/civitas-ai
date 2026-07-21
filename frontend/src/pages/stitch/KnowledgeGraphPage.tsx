import { useQuery } from '@tanstack/react-query'
import { Network, Share2 } from 'lucide-react'
import { api } from '../../services/api'

export default function KnowledgeGraphPage() {
  const { data: summary } = useQuery({ queryKey: ['knowledge-summary'], queryFn: api.getKnowledgeSummary })

  return (
    <div data-testid="knowledge-graph-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Share2 size={22} className="text-primary" /> Knowledge Graph
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Real entity/relation counts from Neo4j — layout is illustrative, counts and sample entities are live.
        </p>
      </div>

      {!summary?.configured && (
        <div className="glass-panel rounded-xl p-6 text-sm text-on-surface-variant">
          Neo4j is <span className="text-tertiary font-semibold">not configured</span> in this environment
          (<code className="text-xs">NEO4J_URI</code> unset) — the graph explorer degrades to this empty state.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
        <div className="glass-panel rounded-xl p-6 flex flex-col items-center justify-center gap-2">
          <Network size={28} className="text-primary" />
          <span data-testid="knowledge-entity-count" className="text-4xl font-black">{summary?.entities ?? 0}</span>
          <span className="text-xs text-outline uppercase tracking-wide">Entities</span>
        </div>
        <div className="glass-panel rounded-xl p-6 flex flex-col items-center justify-center gap-2">
          <Share2 size={28} className="text-secondary" />
          <span data-testid="knowledge-relation-count" className="text-4xl font-black">{summary?.relations ?? 0}</span>
          <span className="text-xs text-outline uppercase tracking-wide">Relations</span>
        </div>
      </div>

      {summary && summary.sample.length > 0 && (
        <div className="glass-panel rounded-xl overflow-hidden">
          <div className="p-4 border-b border-outline-variant bg-surface-container-low">
            <h3 className="text-sm font-semibold">Sample connected entities</h3>
          </div>
          <div className="divide-y divide-outline-variant/30">
            {summary.sample.map((item, i) => (
              <div key={i} data-testid="knowledge-sample-row" className="px-6 py-3 flex items-center justify-between text-sm">
                <div>
                  <span className="font-semibold">{item.name}</span>
                  <span className="text-outline text-xs ml-2">{item.label}</span>
                </div>
                {item.relation && item.related_name && (
                  <span className="text-xs text-on-surface-variant">
                    {item.relation} → {item.related_name}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
