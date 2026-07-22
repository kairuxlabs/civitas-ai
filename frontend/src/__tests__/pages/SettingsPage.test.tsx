import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import SettingsPage from '../../pages/stitch/SettingsPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

beforeEach(() => {
  vi.mocked(api.getSystemStatus).mockResolvedValue({
    database: true,
    gemini_configured: true,
    neo4j_configured: false,
    qdrant_configured: false,
    openrouter_configured: true,
    gemini_model: 'gemini-2.0-flash',
    gemini_temperature: 0.4,
    openrouter_fallback_models: ['nvidia/nemotron-3-ultra-550b-a55b:free', 'openrouter/free'],
  })
})

describe('SettingsPage', () => {
  it('renders the real configured Gemini model and temperature', async () => {
    renderWithQueryClient(<SettingsPage />)
    await waitFor(() => expect(screen.getByTestId('settings-gemini-model')).toHaveTextContent('gemini-2.0-flash'))
    expect(screen.getByTestId('settings-gemini-temperature')).toHaveTextContent('0.4')
  })

  it('lists the real OpenRouter fallback models', async () => {
    renderWithQueryClient(<SettingsPage />)
    await waitFor(() => expect(screen.getAllByTestId('settings-fallback-model')).toHaveLength(2))
  })

  it('shows a loading indicator before the system status query resolves', async () => {
    let resolveStatus: (v: unknown) => void = () => {}
    vi.mocked(api.getSystemStatus).mockImplementation(() => new Promise(resolve => { resolveStatus = resolve }))

    renderWithQueryClient(<SettingsPage />)
    expect(screen.getByTestId('settings-loading')).toBeInTheDocument()

    resolveStatus({
      database: true, gemini_configured: true, neo4j_configured: false,
      qdrant_configured: false, openrouter_configured: true,
      gemini_model: 'gemini-2.0-flash', gemini_temperature: 0.4,
      openrouter_fallback_models: [],
    })
    await waitFor(() => expect(screen.queryByTestId('settings-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the system status query fails', async () => {
    vi.mocked(api.getSystemStatus).mockRejectedValue(new Error('network down'))

    renderWithQueryClient(<SettingsPage />)
    await waitFor(() => expect(screen.getByTestId('settings-error')).toBeInTheDocument())
  })
})
