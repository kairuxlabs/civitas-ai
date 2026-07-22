import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithQueryClient } from '../test-utils'
import KnowledgeGraphPage from '../../pages/stitch/KnowledgeGraphPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

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
    renderWithQueryClient(<KnowledgeGraphPage />)
    await waitFor(() => expect(screen.getByTestId('knowledge-entity-count')).toHaveTextContent('128'))
    expect(screen.getByTestId('knowledge-relation-count')).toHaveTextContent('426')
    expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1)
  })

  it('shows a not-configured state when Neo4j is unset', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: false, entities: 0, relations: 0, sample: [],
    })
    renderWithQueryClient(<KnowledgeGraphPage />)
    await waitFor(() => expect(screen.getByTestId('knowledge-graph-page')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/not configured/i)).toBeInTheDocument())
  })

  it('typing in the search box re-queries the real Neo4j-backed API with the search term', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: twoLabelSample,
    })
    renderWithQueryClient(<KnowledgeGraphPage />)
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(2))

    await userEvent.type(screen.getByTestId('knowledge-search-input'), 'Cau Giay')

    await waitFor(() => expect(api.getKnowledgeSummary).toHaveBeenCalledWith('Cau Giay'))
  })

  it('clicking a label filter chip narrows the sample rows to that entity type', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426, sample: twoLabelSample,
    })
    renderWithQueryClient(<KnowledgeGraphPage />)
    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(2))

    await userEvent.click(screen.getByRole('button', { name: 'Hospital' }))

    await waitFor(() => expect(screen.getAllByTestId('knowledge-sample-row')).toHaveLength(1))
    expect(screen.getByText('Bach Mai Hospital')).toBeInTheDocument()
  })
})
