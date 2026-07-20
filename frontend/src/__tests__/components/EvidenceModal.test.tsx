import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import EvidenceModal from '../../components/EvidenceModal'
import type { EvidenceItem } from '../../types'

const sampleEvidence: EvidenceItem[] = [
  {
    id: 'ev-1', agent: 'traffic', source: 'OpenAQ', type: 'sensor',
    content: 'AQI 180 driving congestion risk', confidence: 0.9, time: '2026-07-20T08:00:00Z',
  },
  {
    id: 'ev-2', agent: 'environment', source: 'OpenAQ', type: 'sensor',
    content: 'AQI 180 (HAZARDOUS)', confidence: 0.9, time: '2026-07-20T08:00:00Z',
  },
  {
    id: 'ev-3', agent: 'knowledge', source: 'SOP', type: 'sop',
    content: 'Air Quality Emergency SOP: Issue health advisory', confidence: 0.9, time: 'static',
  },
]

describe('EvidenceModal', () => {
  it('renders evidence count in header', () => {
    render(<EvidenceModal evidence={sampleEvidence} onClose={vi.fn()} />)
    expect(screen.getByText('3 item(s) supporting this decision')).toBeTruthy()
  })

  it('groups evidence by agent', () => {
    render(<EvidenceModal evidence={sampleEvidence} onClose={vi.fn()} />)
    expect(screen.getByText('Traffic')).toBeTruthy()
    expect(screen.getByText('Environment')).toBeTruthy()
    expect(screen.getByText('Knowledge')).toBeTruthy()
  })

  it('renders source badge and content for each item', () => {
    render(<EvidenceModal evidence={sampleEvidence} onClose={vi.fn()} />)
    expect(screen.getByText('AQI 180 driving congestion risk')).toBeTruthy()
    expect(screen.getAllByText('OpenAQ').length).toBe(2)
    expect(screen.getByText('SOP')).toBeTruthy()
  })

  it('renders confidence as a percentage (0-1 scale multiplied by 100)', () => {
    render(<EvidenceModal evidence={sampleEvidence} onClose={vi.fn()} />)
    expect(screen.getAllByText('90%').length).toBe(3)
  })

  it('shows empty state when evidence is empty', () => {
    render(<EvidenceModal evidence={[]} onClose={vi.fn()} />)
    expect(screen.getByText('No evidence available for this decision.')).toBeTruthy()
  })

  it('calls onClose when the X button is clicked', () => {
    const onClose = vi.fn()
    render(<EvidenceModal evidence={sampleEvidence} onClose={onClose} />)
    const buttons = screen.getAllByRole('button')
    const closeBtn = buttons.find(b => b.querySelector('svg'))
    if (closeBtn) fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })
})
