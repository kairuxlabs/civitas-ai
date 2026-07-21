/**
 * Suite 7 – Remaining Stitch screens (City Intelligence, Reports, Data Sources,
 * Knowledge Graph, Settings). All backend calls mocked; no live backend required.
 */
import { test, expect } from '@playwright/test'
import { waitForApp } from './helpers'

const SYSTEM_STATUS = {
  database: true,
  gemini_configured: true,
  neo4j_configured: false,
  qdrant_configured: true,
  openrouter_configured: false,
  gemini_model: 'gemini-2.0-flash',
  gemini_temperature: 0.4,
  openrouter_fallback_models: ['nvidia/nemotron-3-ultra-550b-a55b:free', 'openrouter/free'],
}

test.describe('Remaining Stitch screens', () => {
  test('City Intelligence shows the real overall score for the selected district', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/aqi/history/**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify([{ time: new Date().toISOString(), aqi_index: 90, pm25: 45 }]),
    }))

    await page.goto('/intelligence')
    await expect(page.getByTestId('city-intelligence-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('city-intelligence-overall-score')).toHaveText('72')
  })

  test('Reports lists real decisions from the timeline and can approve one', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/timeline**', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1, city_id: 'hanoi', district_id: 1, query: 'Prepare for heavy rain',
          prediction: {}, impact: {}, recommendations: [], confidence: 62,
          explanation: [], evidence: [], requires_approval: true, approved: null,
          created_at: new Date().toISOString(),
        },
      ]),
    }))
    let approvedId: number | null = null
    await page.route('**/api/decisions/1/approve', async route => {
      approvedId = 1
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, approved: true }) })
    })

    await page.goto('/reports')
    await expect(page.getByTestId('reports-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('report-row')).toBeVisible()
    await expect(page.getByText('Prepare for heavy rain')).toBeVisible()

    await page.getByTestId('report-approve-button').click()
    await expect.poll(() => approvedId).toBe(1)
  })

  test('Data Sources shows real configured/not-configured integration status', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/system/status', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(SYSTEM_STATUS),
    }))

    await page.goto('/data-sources')
    await expect(page.getByTestId('data-sources-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('data-source-row')).toHaveCount(5)
  })

  test('Knowledge Graph renders real entity/relation counts', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/knowledge/summary', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        configured: true, entities: 128, relations: 426,
        sample: [{
          name: 'Hoan Kiem', label: 'District', relation: 'NEAR', related_name: 'Old Quarter',
          rel_source: 'OSM', rel_confidence: null, rel_created_at: null,
        }],
      }),
    }))

    await page.goto('/knowledge')
    await expect(page.getByTestId('knowledge-graph-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('knowledge-entity-count')).toHaveText('128')
    await expect(page.getByTestId('knowledge-relation-count')).toHaveText('426')
  })

  test('Settings shows the real Gemini model and OpenRouter fallback list', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/system/status', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(SYSTEM_STATUS),
    }))

    await page.goto('/settings')
    await expect(page.getByTestId('settings-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('settings-gemini-model')).toHaveText('gemini-2.0-flash')
    await expect(page.getByTestId('settings-fallback-model')).toHaveCount(2)
  })

  test('sidebar navigation reaches every Stitch screen', async ({ page }) => {
    await waitForApp(page)
    await page.route('**/api/aqi/history/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
    await page.route('**/api/timeline**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
    await page.route('**/api/system/status', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(SYSTEM_STATUS) }))
    await page.route('**/api/knowledge/summary', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ configured: false, entities: 0, relations: 0, sample: [] }),
    }))

    await page.getByRole('link', { name: 'City Intelligence' }).click()
    await expect(page.getByTestId('city-intelligence-page')).toBeVisible({ timeout: 8_000 })

    await page.getByRole('link', { name: 'Reports' }).click()
    await expect(page.getByTestId('reports-page')).toBeVisible({ timeout: 8_000 })

    await page.getByRole('link', { name: 'Data Sources' }).click()
    await expect(page.getByTestId('data-sources-page')).toBeVisible({ timeout: 8_000 })

    await page.getByRole('link', { name: 'Knowledge Graph' }).click()
    await expect(page.getByTestId('knowledge-graph-page')).toBeVisible({ timeout: 8_000 })

    await page.getByRole('link', { name: 'Settings' }).click()
    await expect(page.getByTestId('settings-page')).toBeVisible({ timeout: 8_000 })
  })
})
