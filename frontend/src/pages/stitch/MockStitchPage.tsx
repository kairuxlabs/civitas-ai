export default function MockStitchPage({ title, blurb }: { title: string; blurb: string }) {
  return (
    <div className="p-margin-desktop space-y-4" data-testid="mock-stitch-page">
      <h1 className="text-2xl font-bold text-on-surface">{title}</h1>
      <p className="text-sm text-on-surface-variant max-w-2xl">{blurb}</p>
      <div className="glass-panel rounded-xl p-6 text-sm text-on-surface-variant">
        Layout preview — live data wiring comes in a later phase.
      </div>
    </div>
  )
}
