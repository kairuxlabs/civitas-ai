import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScoreGauge from '../../components/ScoreGauge'

describe('ScoreGauge', () => {
  it('renders the score value rounded', () => {
    render(<ScoreGauge score={75.6} label="Traffic" />)
    expect(screen.getByText('76')).toBeTruthy()
  })

  it('renders the label', () => {
    render(<ScoreGauge score={60} label="Environment" />)
    expect(screen.getByText('Environment')).toBeTruthy()
  })

  it('uses emerald color for score >= 70', () => {
    const { container } = render(<ScoreGauge score={80} label="Test" />)
    const scoreEl = container.querySelector('.text-emerald-400')
    expect(scoreEl).toBeTruthy()
  })

  it('uses yellow color for score 50-69', () => {
    const { container } = render(<ScoreGauge score={55} label="Test" />)
    const scoreEl = container.querySelector('.text-yellow-400')
    expect(scoreEl).toBeTruthy()
  })

  it('uses red color for score < 50', () => {
    const { container } = render(<ScoreGauge score={30} label="Test" />)
    const scoreEl = container.querySelector('.text-red-400')
    expect(scoreEl).toBeTruthy()
  })

  it('renders SVG with two circles (background + progress)', () => {
    const { container } = render(<ScoreGauge score={70} label="Test" />)
    const circles = container.querySelectorAll('circle')
    expect(circles.length).toBe(2)
  })

  it('applies correct stroke-dasharray for 50% score', () => {
    const { container } = render(<ScoreGauge score={50} label="Test" />)
    const progressCircle = container.querySelectorAll('circle')[1]
    const dashArray = progressCircle.getAttribute('stroke-dasharray')
    // r=36, circumference = 2*PI*36 ≈ 226.19, 50% ≈ 113.1
    expect(dashArray).toMatch(/^[\d.]+\s[\d.]+$/)
    const [dash] = dashArray!.split(' ').map(Number)
    expect(dash).toBeCloseTo(113.1, 0)
  })

  it('supports lg size variant with larger radius', () => {
    const { container } = render(<ScoreGauge score={80} label="Test" size="lg" />)
    const progressCircle = container.querySelectorAll('circle')[1]
    expect(progressCircle.getAttribute('r')).toBe('54')
  })
})
