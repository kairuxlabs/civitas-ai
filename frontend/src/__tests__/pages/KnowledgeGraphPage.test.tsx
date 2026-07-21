import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithQueryClient } from '../test-utils'
import KnowledgeGraphPage from '../../pages/stitch/KnowledgeGraphPage'
import { api } from '../../services/api'

vi.mock('../../services/api')

describe('KnowledgeGraphPage', () => {
  it('renders real entity/relation counts when Neo4j is configured', async () => {
    vi.mocked(api.getKnowledgeSummary).mockResolvedValue({
      configured: true, entities: 128, relations: 426,
      sample: [{
        name: 'Hoan Kiem', label: 'District', relation: 'NEAR', related_name: 'Old Quarter',
        rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
      }],
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
})
