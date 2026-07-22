import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import DataSourcesPage from '../../pages/stitch/DataSourcesPage'
import { api } from '../../services/api'
import { LanguageProvider } from '../../i18n/LanguageContext'

vi.mock('../../services/api')

function renderPage() {
  return renderWithQueryClient(<LanguageProvider><DataSourcesPage /></LanguageProvider>)
}

beforeEach(() => {
  vi.mocked(api.getHealth).mockResolvedValue({ status: 'ok' })
  vi.mocked(api.getSystemStatus).mockResolvedValue({
    database: true,
    gemini_configured: true,
    neo4j_configured: false,
    qdrant_configured: true,
    openrouter_configured: false,
    gemini_model: 'gemini-2.0-flash',
    gemini_temperature: 0.4,
    openrouter_fallback_models: ['nvidia/nemotron-3-ultra-550b-a55b:free'],
  })
})

describe('DataSourcesPage', () => {
  it('renders real configured/not-configured status for each integration', async () => {
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('data-source-row')).toHaveLength(5))
    // Match the source-name cell exactly — the Gemini row's own type column now
    // legitimately contains the model slug "gemini-2.0-flash", which a loose
    // /gemini/i text search would also match once the page waits for real data.
    const neo4jRow = screen.getByText('Neo4j').closest('[data-testid="data-source-row"]')!
    expect(neo4jRow).toHaveTextContent(/not configured/i)
    const geminiRow = screen.getByText('Gemini').closest('[data-testid="data-source-row"]')!
    expect(geminiRow).toHaveTextContent(/configured/i)
  })

  it('shows a loading indicator before the system status query resolves', async () => {
    let resolveStatus: (v: unknown) => void = () => {}
    vi.mocked(api.getSystemStatus).mockImplementation(() => new Promise(resolve => { resolveStatus = resolve }))

    renderPage()
    expect(screen.getByTestId('data-sources-loading')).toBeInTheDocument()

    resolveStatus({
      database: true, gemini_configured: true, neo4j_configured: false,
      qdrant_configured: true, openrouter_configured: false,
      gemini_model: 'gemini-2.0-flash', gemini_temperature: 0.4,
      openrouter_fallback_models: [],
    })
    await waitFor(() => expect(screen.queryByTestId('data-sources-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the system status query fails', async () => {
    vi.mocked(api.getSystemStatus).mockRejectedValue(new Error('network down'))

    renderPage()
    await waitFor(() => expect(screen.getByTestId('data-sources-error')).toBeInTheDocument())
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    localStorage.setItem('civitas-language', 'vi')
    renderPage()

    await waitFor(() => expect(screen.getByText('Nguồn dữ liệu & Tình trạng')).toBeInTheDocument())
    localStorage.removeItem('civitas-language')
  })
})
