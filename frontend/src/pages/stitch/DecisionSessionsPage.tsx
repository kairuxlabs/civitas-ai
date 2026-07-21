import DecisionSessionsPanel from '../../components/DecisionSessionsPanel'

export default function DecisionSessionsPage() {
  return (
    <div data-testid="decision-sessions-page" className="p-margin-desktop space-y-gutter pb-16">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Decision Sessions</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Track goal lifecycle from submission through observed CityScore outcomes.
        </p>
      </div>
      <DecisionSessionsPanel />
    </div>
  )
}
