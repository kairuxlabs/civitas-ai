import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import AppShell from '../../layout/AppShell'
import { LanguageProvider } from '../../i18n/LanguageContext'

function renderShell() {
  return render(
    <LanguageProvider>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<div>Overview outlet</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </LanguageProvider>,
  )
}

describe('AppShell', () => {
  it('renders sidebar nav links for phase-1 routes', () => {
    renderShell()
    expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Workspace' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Decision Sessions' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Command Center' })).not.toBeInTheDocument()
    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
  })

  it('clicking the VI button switches nav labels to Vietnamese', async () => {
    const user = userEvent.setup()
    renderShell()

    await user.click(screen.getByTestId('lang-switch-vi'))

    expect(screen.getByRole('link', { name: 'Tổng quan' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Không gian quyết định' })).toBeInTheDocument()
  })

  it('clicking EN after VI switches back to English', async () => {
    const user = userEvent.setup()
    renderShell()

    await user.click(screen.getByTestId('lang-switch-vi'))
    await user.click(screen.getByTestId('lang-switch-en'))

    expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument()
  })
})
