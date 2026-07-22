import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import KnowledgeGraphPage from '../../pages/stitch/KnowledgeGraphPage'
import { api } from '../../services/api'
import { LanguageProvider } from '../../i18n/LanguageContext'

vi.mock('../../services/api')

function renderPage() {
  return renderWithQueryClient(<LanguageProvider><KnowledgeGraphPage /></LanguageProvider>)
}

const twoLabelSample = [
  {
    name: 'Hoan Kiem', label: 'District', relation: 'NEAR', related_name: 'Old Quarter',
    rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
  },
  {
    name: 'Bach Mai Hospital', label: 'Hospital', relation: 'IN', related_name: 'Hai Ba Trung',
    rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
  },
]

describe('KnowledgeGraphPage', () => {
  it('renders real entity/relation counts when Neo4j is configured', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426,
      sample: [twoLabelSample[0]],
    })
    renderPage()
    await waitFor(() => expect(screen.getByTestId('knowledge-entity-count')).toHaveTextContent('128'))
    expect(screen.getByTestId('knowledge-relation-count')).toHaveTextContent('426')
    expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1)
  })

  it('shows a not-configured state when Neo4j is unset', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: false, entities: 0, relations: 0, sample: [],
    })
    renderPage()
    await waitFor(() => expect(screen.getByTestId('knowledge-graph-page')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/not configured/i)).toBeInTheDocument())
  })

  it('shows an empty-state message when Neo4j is configured but the sample is empty', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 0, relations: 0, sample: [],
    })
    renderPage()
    await waitFor(() => expect(screen.getByTestId('knowledge-graph-empty')).toBeInTheDocument())
    expect(screen.queryByTestId('knowledge-sample-row')).not.toBeInTheDocument()
  })

  it('typing in the search box re-queries the real Neo4j-backed API with the search term', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: twoLabelSample,
    })
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(2))

    await userEvent.type(screen.getByTestId('knowledge-search-input'), 'Cau Giay')

    await waitFor(() => expect(api.getKnowledgeSummary).toHaveBeenCalledWith('Cau Giay'))
  })

  it('clicking a label filter chip narrows the sample rows to that entity type', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: twoLabelSample,
    })
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(2))

    await userEvent.click(screen.getByRole('button', { name: 'Hospital' }))

    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))
    expect(screen.getByText('Bach Mai Hospital')).toBeInTheDocument()
  })

  it('shows a loading indicator before the knowledge summary query resolves, without unmounting the search input', async () => {
    let resolveSummary: (v: unknown) => void = () => {}
    vi.mocked(api.getKnowledgeSummary).mockImplementation(() => new Promise(resolve => { resolveSummary = resolve }))

    renderPage()
    expect(screen.getByTestId('knowledge-graph-loading')).toBeInTheDocument()
    // Search input must stay mounted during loading so typing isn't interrupted
    expect(screen.getByTestId('knowledge-search-input')).toBeInTheDocument()

    resolveSummary({ configured: true, entities: 0, relations: 0, sample: [] })
    await waitFor(() => expect(screen.queryByTestId('knowledge-graph-loading')).not.toBeInTheDocument())
  })

  it('shows an inline error when the knowledge summary query fails', async () => {
    vi.mocked(api.getKnowledgeSummary).mockRejectedValue(new Error('network down'))

    renderPage()
    await waitFor(() => expect(screen.getByTestId('knowledge-graph-error')).toBeInTheDocument())
  })

  it('renders Vietnamese labels when the language is switched to vi', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({ configured: false, entities: 0, relations: 0, sample: [] })
    localStorage.setItem('civitas-language', 'vi')

    renderPage()

    await waitFor(() => expect(screen.getByText('Đồ thị tri thức')).toBeInTheDocument())
    localStorage.removeItem('civitas-language')
  })
})
