export default function MockStitchPage({ title, blurb }: { title: string; blurb: string }) {
  return (
    <div className="p-margin-desktop space-y-4" data-testid="mock-stitch-page">
      <h1 className="text-2xl font-bold text-on-surface">{title}</h1>
      <p className="text-sm text-on-surface-variant max-w-2xl">{blurb}</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
        {['Signals', 'Coverage', 'Notes'].map(label => (
          <div key={label} className="glass-panel rounded-xl p-4">
            <p className="text-xs text-on-surface-variant mb-2">{label}</p>
            <p className="text-sm text-on-surface">Mock content for phase 1 layout.</p>
          </div>
        ))}
      </div>
    </div>
  )
}
