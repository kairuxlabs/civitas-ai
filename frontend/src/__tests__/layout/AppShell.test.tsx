import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import AppShell from '../../layout/AppShell'

describe('AppShell', () => {
  it('renders sidebar nav links for phase-1 routes', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<div>Overview outlet</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Workspace' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Sessions' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Command Center' })).not.toBeInTheDocument()
    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
  })
})
