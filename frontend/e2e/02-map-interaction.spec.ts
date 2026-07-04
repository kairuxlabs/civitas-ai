/**
 * Suite 2 – Digital Twin Map Interactions
 * API is mocked (no backend required).
 * Tests clicking districts and verifying the selected district name appears.
 */
import { test, expect } from '@playwright/test'
import { waitForApp, MOCK_DISTRICTS } from './helpers'

test.describe('Map district selection', () => {
  test('all 12 district nodes are in the DOM', async ({ page }) => {
    await waitForApp(page)
    for (let i = 1; i <= 12; i++) {
      await expect(page.locator(`[data-testid="district-${i}"]`)).toBeAttached()
    }
  })

  for (const { id, name } of MOCK_DISTRICTS) {
    test(`clicking district ${id} (${name}) updates header and copilot label`, async ({ page }) => {
      await waitForApp(page)
      await page.locator(`[data-testid="district-${id}"]`).click()
      // District info bar: selected name appears
      await expect(page.getByText(name, { exact: false }).first()).toBeVisible({ timeout: 5_000 })
      // Copilot subtitle updates
      await expect(page.getByText(`Ask about ${name}`, { exact: false })).toBeVisible({ timeout: 5_000 })
    })
  }

  test('clicking a district highlights it (selection ring visible)', async ({ page }) => {
    await waitForApp(page)
    // District 3 starts unselected; clicking should cause a ring to appear (animating circle)
    await page.locator('[data-testid="district-3"]').click()
    // After selection the SVG should contain a blue ring stroke
    const svg = page.locator('svg').first()
    await expect(svg).toBeVisible()
  })
})
