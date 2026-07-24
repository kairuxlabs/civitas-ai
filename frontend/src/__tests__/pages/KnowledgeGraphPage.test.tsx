import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
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
  beforeEach(() => {
    vi.mocked(api.getKnowledgeLabels).mockResolvedValue([])
  })

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

  it('clicking a sample row opens a detail modal with that entity\'s full relation list', async () => {
    vi.mocked(api.getKnowledgeSummary).mockImplementation(async (q) => {
      if (q === 'Hoan Kiem') {
        return {
          configured: true, entities: 128, relations: 426,
          sample: [
            {
              name: 'Hoan Kiem', label: 'District', relation: 'NEAR', related_name: 'Old Quarter',
              rel_source: 'OSM', rel_confidence: 0.9, rel_created_at: '2026-07-20T10:00:00Z',
            },
            {
              name: 'Hoan Kiem', label: 'District', relation: 'CONTAINS', related_name: 'Hoan Kiem Lake',
              rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
            },
          ],
        }
      }
      return { configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]] }
    })

    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))

    await user.click(screen.getByText('Hoan Kiem'))

    await waitFor(() => expect(screen.getByTestId('knowledge-entity-modal')).toBeInTheDocument())
    await waitFor(() => expect(screen.getAllByTestId('knowledge-entity-relation-row')).toHaveLength(2))
    expect(screen.getByText(/CONTAINS/)).toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()
  })

  it('shows an empty state in the entity modal when the drill-down query returns no relations', async () => {
    vi.mocked(api.getKnowledgeSummary).mockImplementation(async (q) => {
      if (q === 'Hoan Kiem') return { configured: true, entities: 128, relations: 426, sample: [] }
      return { configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]] }
    })

    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))

    await user.click(screen.getByText('Hoan Kiem'))

    await waitFor(() => expect(screen.getByTestId('knowledge-entity-empty')).toBeInTheDocument())
  })

  it('closes the entity detail modal via the close button', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]],
    })

    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))

    await user.click(screen.getByText('Hoan Kiem'))
    await waitFor(() => expect(screen.getByTestId('knowledge-entity-modal')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Close' }))
    await waitFor(() => expect(screen.queryByTestId('knowledge-entity-modal')).not.toBeInTheDocument())
  })

  it('shows the no-relations empty state instead of a blank row when the entity has no real relations', async () => {
    vi.mocked(api.getKnowledgeSummary).mockImplementation(async (q) => {
      if (q === 'Hoan Kiem') {
        return {
          configured: true, entities: 128, relations: 426,
          sample: [
            {
              name: 'Hoan Kiem', label: 'District', relation: null, related_name: null,
              rel_source: null, rel_confidence: null, rel_created_at: null,
            },
          ],
        }
      }
      return { configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]] }
    })

    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))

    await user.click(screen.getByText('Hoan Kiem'))

    await waitFor(() => expect(screen.getByTestId('knowledge-entity-empty')).toBeInTheDocument())
    expect(screen.queryByTestId('knowledge-entity-relation-row')).not.toBeInTheDocument()
    const modal = within(screen.getByTestId('knowledge-entity-modal'))
    expect(modal.queryByText('—', { exact: false })).not.toBeInTheDocument()
  })

  it('shows a per-label icon next to each sample entity row', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]],
    })
    renderPage()
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))
    const row = screen.getByTestId('knowledge-sample-row')
    expect(row.querySelector('svg')).toBeInTheDocument()
  })

  it('shows label chips with counts and lists entities when a chip is clicked', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]],
    })
    vi.mocked(api.getKnowledgeLabels).mockResolvedValue([
      { label: 'District', count: 12 },
      { label: 'Hospital', count: 8 },
    ])
    vi.mocked(api.getKnowledgeEntities).mockResolvedValue([
      { name: 'Hoan Kiem', display_name: 'Hoan Kiem District' },
    ])

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getAllByTestId('knowledge-browse-label-chip')).toHaveLength(2))
    expect(screen.getByText('District (12)')).toBeInTheDocument()
    expect(screen.getByText('Hospital (8)')).toBeInTheDocument()

    await user.click(screen.getByText('District (12)'))

    await waitFor(() => expect(screen.getByTestId('knowledge-browse-entity-row')).toBeInTheDocument())
    expect(api.getKnowledgeEntities).toHaveBeenCalledWith('District', 50)
    expect(screen.getByText('Hoan Kiem District')).toBeInTheDocument()
  })

  it('clicking a browsed entity opens its detail modal', async () => {
    vi.mocked(api.getKnowledgeSummary).mockImplementation(async (q) => {
      if (q === 'Hoan Kiem') {
        return {
          configured: true, entities: 128, relations: 426,
          sample: [
            {
              name: 'Hoan Kiem', label: 'District', relation: 'NEAR', related_name: 'Old Quarter',
              rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
            },
          ],
        }
      }
      return { configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]] }
    })
    vi.mocked(api.getKnowledgeLabels).mockResolvedValue([{ label: 'District', count: 12 }])
    vi.mocked(api.getKnowledgeEntities).mockResolvedValue([{ name: 'Hoan Kiem', display_name: 'Hoan Kiem District' }])

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('knowledge-browse-label-chip')).toBeInTheDocument())
    await user.click(screen.getByText('District (12)'))
    await waitFor(() => expect(screen.getByTestId('knowledge-browse-entity-row')).toBeInTheDocument())

    await user.click(screen.getByText('Hoan Kiem District'))

    await waitFor(() => expect(screen.getByTestId('knowledge-entity-modal')).toBeInTheDocument())
  })

  it('shows an empty state when a label has no entities', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: [twoLabelSample[0]],
    })
    vi.mocked(api.getKnowledgeLabels).mockResolvedValue([{ label: 'District', count: 0 }])
    vi.mocked(api.getKnowledgeEntities).mockResolvedValue([])

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => expect(screen.getByTestId('knowledge-browse-label-chip')).toBeInTheDocument())
    await user.click(screen.getByText('District (0)'))

    await waitFor(() => expect(screen.getByText('No entities found for this type yet.')).toBeInTheDocument())
  })
})
