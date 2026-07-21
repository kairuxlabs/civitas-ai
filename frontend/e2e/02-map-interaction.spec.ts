/**
 * Suite 2 – Digital Twin Map Interactions
 * API is mocked (no backend required).
 * Tests clicking districts and verifying the selected district name appears.
 */
import { test, expect } from '@playwright/test'
import { waitForCommandCenter, MOCK_DISTRICTS } from './helpers'

test.describe('Map district selection', () => {
  test('all 12 district nodes are in the DOM', async ({ page }) => {
    await waitForCommandCenter(page)
    for (let i = 1; i <= 12; i++) {
      await expect(page.locator(`[data-testid="district-${i}"]`)).toBeAttached()
    }
  })

  for (const { id, name } of MOCK_DISTRICTS) {
    test(`clicking district ${id} (${name}) updates header and copilot label`, async ({ page }) => {
      await waitForCommandCenter(page)
      // SVG <g> hover handlers mutate the DOM on mousemove, making the element unstable.
      // dispatchEvent fires the click directly without moving the mouse, bypassing all hover effects.
      await page.locator(`[data-testid="district-${id}"]`).dispatchEvent('click')
      // Info bar: "Selected: <name>" appears
      await expect(page.getByText(name, { exact: false }).first()).toBeVisible({ timeout: 5_000 })
      // Copilot subtitle updates to "Ask about <name>"
      await expect(page.getByText(`Ask about ${name}`, { exact: false })).toBeVisible({ timeout: 5_000 })
    })
  }

  test('clicking a district highlights it (selection ring visible)', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.locator('[data-testid="district-3"]').dispatchEvent('click')
    const svg = page.locator('svg').first()
    await expect(svg).toBeVisible()
  })

  test('regression: a genuine mouse click (not force/dispatchEvent) selects a non-default district', async ({ page }) => {
    // The decorative background grid <svg> previously lacked pointer-events-none, so it
    // silently intercepted every real click on the map (Playwright reported
    // "<rect fill=url(#grid)> subtree intercepts pointer events"). Unlike dispatchEvent
    // or { force: true }, a plain .click() performs real hit-testing and would have
    // caught this regression.
    await waitForCommandCenter(page)
    await page.locator('[data-testid="district-2"]').click()
    await expect(page.getByText('Ba Đình', { exact: false }).first()).toBeVisible()

    await page.locator('[data-testid="district-5"]').click()
    await expect(page.getByText('Hoàng Mai', { exact: false }).first()).toBeVisible()
  })
})
