/**
 * Suite 8 – Production smoke test (live Vercel frontend + live Render backend + real DB/Neo4j/Qdrant).
 * No mocks. Read-only checks only — never submits goals, approves/rejects, or triggers observations,
 * since this hits real production data. Skips automatically if the live site isn't reachable.
 */
import { test, expect } from '@playwright/test'

const PROD_URL = 'https://frontend-eta-six-46.vercel.app'
const BACKEND_URL = 'https://civitas-ai-backend.onrender.com'

test.describe('Production smoke test', () => {
  test.beforeEach(async ({ page }) => {
    const alive = await page.request.get(`${BACKEND_URL}/health`, { timeout: 15_000 }).then(r => r.ok()).catch(() => false)
    test.skip(!alive, 'Production backend not reachable — skipping live smoke test')
  })

  test('Overview renders with real district scores', async ({ page }) => {
    await page.goto(`${PROD_URL}/`)
    await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByTestId('overview-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('overview-overall-score')).not.toHaveText('—', { timeout: 15_000 })
  })

  test('Decision Workspace loads the goal input (read-only)', async ({ page }) => {
    await page.goto(`${PROD_URL}/workspace`)
    await expect(page.getByTestId('decision-workspace-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByPlaceholder(/Reduce congestion/i)).toBeVisible()
  })

  test('Decision Sessions renders real session cards', async ({ page }) => {
    await page.goto(`${PROD_URL}/sessions`)
    await expect(page.getByTestId('decision-sessions-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('decision-session-card').first()).toBeVisible({ timeout: 15_000 })
  })

  test('Command Center loads inside the shell', async ({ page }) => {
    await page.goto(`${PROD_URL}/command-center`)
    await expect(page.getByTestId('command-center-route')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('app-header')).toBeVisible({ timeout: 15_000 })
  })

  test('Data Sources shows all integrations as configured', async ({ page }) => {
    await page.goto(`${PROD_URL}/data-sources`)
    await expect(page.getByTestId('data-sources-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('data-source-row')).toHaveCount(5, { timeout: 15_000 })
    await expect(page.getByText('Not configured')).toHaveCount(0)
  })

  test('Knowledge Graph shows real, non-zero entity/relation counts', async ({ page }) => {
    await page.goto(`${PROD_URL}/knowledge`)
    await expect(page.getByTestId('knowledge-graph-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('knowledge-entity-count')).not.toHaveText('0', { timeout: 15_000 })
    const entityText = await page.getByTestId('knowledge-entity-count').innerText()
    expect(Number(entityText)).toBeGreaterThan(0)
  })

  test('City Intelligence shows a real overall score for Hoan Kiem', async ({ page }) => {
    await page.goto(`${PROD_URL}/intelligence`)
    await expect(page.getByTestId('city-intelligence-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('city-intelligence-overall-score')).not.toHaveText('—', { timeout: 15_000 })
  })

  test('Reports lists real decision history', async ({ page }) => {
    await page.goto(`${PROD_URL}/reports`)
    await expect(page.getByTestId('reports-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('report-row').first()).toBeVisible({ timeout: 15_000 })
  })

  test('Settings shows the real Gemini model in use', async ({ page }) => {
    await page.goto(`${PROD_URL}/settings`)
    await expect(page.getByTestId('settings-page')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('settings-gemini-model')).toHaveText('gemini-2.0-flash', { timeout: 15_000 })
  })

  test('sidebar navigation reaches every screen in production', async ({ page }) => {
    await page.goto(`${PROD_URL}/`)
    await expect(page.getByTestId('overview-page')).toBeVisible({ timeout: 20_000 })

    for (const label of ['Decision Workspace', 'Decision Sessions', 'Data Sources', 'Knowledge Graph', 'City Intelligence', 'Reports', 'Settings']) {
      await page.getByRole('link', { name: label }).click()
      await expect(page.getByTestId('app-shell')).toBeVisible()
    }
  })
})
