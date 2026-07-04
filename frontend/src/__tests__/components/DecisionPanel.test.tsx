import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DecisionPanel from '../../components/DecisionPanel'
import type { DecisionOut } from '../../types'

const sampleDecision: DecisionOut = {
  prediction: { flood_risk: 'high', next_6h_aqi_trend: 'increasing' },
  impact: { population_affected: '100,000 residents', economic_impact: 'high' },
  recommendations: ['Activate flood drainage', 'Issue health advisory'],
  confidence: 78,
  explanation: ['Traffic Analysis: HIGH congestion', 'Confidence: 78%'],
}

describe('DecisionPanel', () => {
  it('shows placeholder when decision is null', () => {
    render(<DecisionPanel decision={null} />)
    expect(screen.getByText('No analysis yet.')).toBeTruthy()
  })

  it('shows loading skeleton when loading=true', () => {
    const { container } = render(<DecisionPanel decision={null} loading />)
    const skeleton = container.querySelector('.animate-pulse')
    expect(skeleton).toBeTruthy()
  })

  it('renders confidence percentage', () => {
    render(<DecisionPanel decision={sampleDecision} />)
    expect(screen.getByText('78%')).toBeTruthy()
  })

  it('renders all recommendations', () => {
    render(<DecisionPanel decision={sampleDecision} />)
    expect(screen.getByText('Activate flood drainage')).toBeTruthy()
    expect(screen.getByText('Issue health advisory')).toBeTruthy()
  })

  it('renders explanation items', () => {
    render(<DecisionPanel decision={sampleDecision} />)
    expect(screen.getByText('Traffic Analysis: HIGH congestion')).toBeTruthy()
    expect(screen.getByText('Confidence: 78%')).toBeTruthy()
  })

  it('renders confidence progress bar width proportional to confidence', () => {
    const { container } = render(<DecisionPanel decision={sampleDecision} />)
    const bar = container.querySelector('.bg-blue-500.rounded-full') as HTMLElement | null
    expect(bar?.style.width).toBe('78%')
  })

  it('rounds confidence when not integer', () => {
    const dec = { ...sampleDecision, confidence: 82.7 }
    render(<DecisionPanel decision={dec} />)
    expect(screen.getByText('83%')).toBeTruthy()
  })
})
