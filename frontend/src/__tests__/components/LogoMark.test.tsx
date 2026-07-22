import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import LogoMark from '../../components/LogoMark'

describe('LogoMark', () => {
  it('renders an SVG mark', () => {
    const { getByTestId } = render(<LogoMark />)
    expect(getByTestId('logo-mark').tagName.toLowerCase()).toBe('svg')
  })

  it('respects a custom size', () => {
    const { getByTestId } = render(<LogoMark size={40} />)
    expect(getByTestId('logo-mark')).toHaveAttribute('width', '40')
    expect(getByTestId('logo-mark')).toHaveAttribute('height', '40')
  })
})
