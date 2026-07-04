import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AgentGraph from '../../components/AgentGraph'
import type { AgentEvent } from '../../types'

const makeEvent = (
  type: AgentEvent['type'],
  agent: string,
  status: AgentEvent['status'],
): AgentEvent => ({ type, agent, status, detail: '', ts: '2024-01-01T00:00:00Z' })

describe('AgentGraph', () => {
  it('renders the SVG container', () => {
    const { container } = render(<AgentGraph events={[]} />)
    expect(container.querySelector('svg')).toBeTruthy()
  })

  it('shows "Waiting for query..." when no events', () => {
    render(<AgentGraph events={[]} />)
    expect(screen.getByText('Waiting for query...')).toBeTruthy()
  })

  it('shows pipeline running status after pipeline_start', () => {
    const events: AgentEvent[] = [
      makeEvent('pipeline_start', 'Supervisor', 'planning'),
    ]
    render(<AgentGraph events={events} />)
    expect(screen.getByText('⟳ Pipeline running...')).toBeTruthy()
  })

  it('shows pipeline complete after pipeline_done', () => {
    const events: AgentEvent[] = [
      makeEvent('pipeline_start', 'Supervisor', 'planning'),
      makeEvent('pipeline_done', 'Supervisor', 'done'),
    ]
    render(<AgentGraph events={events} />)
    expect(screen.getByText('✓ Pipeline complete')).toBeTruthy()
  })

  it('renders all 7 pipeline agent labels', () => {
    render(<AgentGraph events={[]} />)
    const expected = ['Traffic', 'Environment', 'Event', 'Citizen', 'Knowledge', 'Decision', 'Explanation']
    for (const name of expected) {
      expect(screen.getByText(name)).toBeTruthy()
    }
  })

  it('renders Supervisor node label', () => {
    render(<AgentGraph events={[]} />)
    expect(screen.getByText('Supervisor')).toBeTruthy()
  })

  it('renders check mark on done agent', () => {
    const events: AgentEvent[] = [
      makeEvent('pipeline_start', 'Supervisor', 'planning'),
      makeEvent('agent_update', 'Traffic Agent', 'done'),
    ]
    const { container } = render(<AgentGraph events={events} />)
    // The ✓ glyph should appear for the done agent
    const texts = container.querySelectorAll('text')
    const checkTexts = Array.from(texts).filter(t => t.textContent === '✓')
    expect(checkTexts.length).toBeGreaterThanOrEqual(1)
  })
})
