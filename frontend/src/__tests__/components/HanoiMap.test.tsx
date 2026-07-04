import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import HanoiMap from '../../components/HanoiMap'
import type { CityScore } from '../../types'

const makeScore = (districtId: number, overall: number, risk = 30): CityScore => ({
  id: districtId,
  city_id: 'hanoi',
  district_id: districtId,
  timestamp: '2024-01-01T00:00:00Z',
  traffic_score: overall,
  environment_score: overall,
  citizen_score: 70,
  risk_score: risk,
  overall_score: overall,
})

describe('HanoiMap', () => {
  it('renders an SVG element', () => {
    const { container } = render(
      <HanoiMap scores={[]} selectedDistrictId={null} onSelectDistrict={() => {}} />
    )
    expect(container.querySelector('svg')).toBeTruthy()
  })

  it('renders 12 district nodes', () => {
    const { container } = render(
      <HanoiMap scores={[]} selectedDistrictId={null} onSelectDistrict={() => {}} />
    )
    // Each district is rendered as a <g> with a <circle> inside
    const circles = container.querySelectorAll('circle[r="26"], circle[r="28"], circle[r="30"], circle[r="32"]')
    // At least 12 main district circles
    expect(circles.length).toBeGreaterThanOrEqual(12)
  })

  it('shows score text for a district with data', () => {
    const scores = [makeScore(1, 82)]
    render(
      <HanoiMap scores={scores} selectedDistrictId={1} onSelectDistrict={() => {}} />
    )
    // District 1 (Hoàn Kiếm) should show score "82"
    expect(screen.getByText('82')).toBeTruthy()
  })

  it('calls onSelectDistrict when a district node is clicked', () => {
    const onSelect = vi.fn()
    const { container } = render(
      <HanoiMap scores={[]} selectedDistrictId={null} onSelectDistrict={onSelect} />
    )
    // All district <g> elements have style="cursor: pointer"
    const clickableGroups = Array.from(container.querySelectorAll('g')).filter(g =>
      (g.getAttribute('style') ?? '').includes('cursor: pointer')
    )
    expect(clickableGroups.length).toBeGreaterThanOrEqual(12)
    fireEvent.click(clickableGroups[0])
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(expect.any(Number))
  })

  it('background grid overlay does not intercept clicks (pointer-events-none)', () => {
    // Regression test: the decorative grid <svg> is absolutely positioned, so it paints
    // above the (statically positioned) map <svg> regardless of DOM order. Without
    // pointer-events-none it silently swallows every click aimed at district nodes.
    const { container } = render(
      <HanoiMap scores={[]} selectedDistrictId={null} onSelectDistrict={() => {}} />
    )
    const svgs = container.querySelectorAll('svg')
    const gridSvg = Array.from(svgs).find(s => s.querySelector('rect[fill="url(#grid)"]'))
    expect(gridSvg).toBeTruthy()
    expect(gridSvg?.getAttribute('class')).toContain('pointer-events-none')
  })

  it('renders legend items', () => {
    const { container } = render(
      <HanoiMap scores={[]} selectedDistrictId={null} onSelectDistrict={() => {}} />
    )
    const texts = Array.from(container.querySelectorAll('text')).map(t => t.textContent ?? '')
    expect(texts.some(t => t.includes('Good'))).toBe(true)
    expect(texts.some(t => t.includes('Fair'))).toBe(true)
    expect(texts.some(t => t.includes('Poor') || t.includes('At Risk'))).toBe(true)
  })

  it('applies green fill for score >= 80', () => {
    const scores = [makeScore(1, 85)]
    const { container } = render(
      <HanoiMap scores={scores} selectedDistrictId={1} onSelectDistrict={() => {}} />
    )
    const circles = container.querySelectorAll('circle')
    const greenCircle = Array.from(circles).find(c => c.getAttribute('fill') === '#22c55e')
    expect(greenCircle).toBeTruthy()
  })

  it('applies red fill for score < 60', () => {
    const scores = [makeScore(1, 45)]
    const { container } = render(
      <HanoiMap scores={scores} selectedDistrictId={1} onSelectDistrict={() => {}} />
    )
    const circles = container.querySelectorAll('circle')
    const redCircle = Array.from(circles).find(c => c.getAttribute('fill') === '#ef4444')
    expect(redCircle).toBeTruthy()
  })
})
