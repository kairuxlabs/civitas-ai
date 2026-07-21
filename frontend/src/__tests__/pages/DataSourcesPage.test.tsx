import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import DataSourcesPage from '../../pages/stitch/DataSourcesPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

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
    renderWithQueryClient(<DataSourcesPage />)
    await waitFor(() => expect(screen.getAllByTestId('data-source-row')).toHaveLength(5))
    const neo4jRow = screen.getByText(/neo4j/i).closest('[data-testid="data-source-row"]')!
    expect(neo4jRow).toHaveTextContent(/not configured/i)
    const geminiRow = screen.getByText(/gemini/i).closest('[data-testid="data-source-row"]')!
    expect(geminiRow).toHaveTextContent(/configured/i)
  })
})
