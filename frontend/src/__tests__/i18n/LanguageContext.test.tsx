import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LanguageProvider, useLanguage } from '../../i18n/LanguageContext'
import { useTranslation } from '../../i18n/useTranslation'

function Probe() {
  const { language, setLanguage } = useLanguage()
  const { t } = useTranslation()
  return (
    <div>
      <span data-testid="current-lang">{language}</span>
      <span data-testid="translated">{t('nav.overview')}</span>
      <button onClick={() => setLanguage('vi')}>switch</button>
    </div>
  )
}

beforeEach(() => {
  localStorage.clear()
})

describe('LanguageContext', () => {
  it('defaults to English', () => {
    render(<LanguageProvider><Probe /></LanguageProvider>)
    expect(screen.getByTestId('current-lang')).toHaveTextContent('en')
    expect(screen.getByTestId('translated')).toHaveTextContent('Overview')
  })

  it('switching language re-renders with the new translation and persists to localStorage', async () => {
    const user = userEvent.setup()
    render(<LanguageProvider><Probe /></LanguageProvider>)

    await user.click(screen.getByRole('button', { name: 'switch' }))

    expect(screen.getByTestId('current-lang')).toHaveTextContent('vi')
    expect(screen.getByTestId('translated')).toHaveTextContent('Tổng quan')
    expect(localStorage.getItem('civitas-language')).toBe('vi')
  })

  it('restores a persisted language on mount', () => {
    localStorage.setItem('civitas-language', 'vi')
    render(<LanguageProvider><Probe /></LanguageProvider>)
    expect(screen.getByTestId('current-lang')).toHaveTextContent('vi')
  })
})
