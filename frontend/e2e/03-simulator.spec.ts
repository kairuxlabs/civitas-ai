/**
 * Suite 3 – Simulator Modal UI
 * Does NOT require the backend. Tests the modal open/close/select flow
 * and mocks the /api/simulate endpoint so the pipeline progress is testable.
 */
import { test, expect } from '@playwright/test'
import { waitForApp } from './helpers'

test.describe('Simulator modal', () => {
  test('opens when clicking Mô phỏng button', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-modal')).toBeVisible()
    await expect(page.getByText('What-If Simulator')).toBeVisible()
  })

  test('closes when clicking X button', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-modal')).toBeVisible()
    await page.locator('[data-testid="simulator-modal"] button').filter({ hasText: '' }).first().click()
    await expect(page.getByTestId('simulator-modal')).not.toBeVisible()
  })

  test('shows 4 scenario cards', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('scenario-heavy_rain')).toBeVisible()
    await expect(page.getByTestId('scenario-air_pollution')).toBeVisible()
    await expect(page.getByTestId('scenario-major_event')).toBeVisible()
    await expect(page.getByTestId('scenario-heatwave')).toBeVisible()
  })

  test('Run button is disabled before selecting a scenario', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-run-btn')).toBeDisabled()
  })

  test('Run button enables after selecting a scenario', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heavy_rain').click()
    await expect(page.getByTestId('simulator-run-btn')).toBeEnabled()
  })

  test('selecting different scenario changes active card', async ({ page }) => {
    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heatwave').click()
    // Heatwave card should have scale-[1.02] applied (selected state)
    const card = page.getByTestId('scenario-heatwave')
    await expect(card).toHaveClass(/border-red-500/)
  })

  test('shows pipeline steps view after clicking Run (with mocked API)', async ({ page }) => {
    // Mock the simulate endpoint so we don't need a running backend
    await page.route('**/api/simulate', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          prediction: { flood_risk: 'high' },
          impact: { traffic: 'severe' },
          recommendations: ['Evacuate low areas'],
          confidence: 88,
          explanation: ['Heavy rain detected', 'Flood risk elevated'],
          evidence: [],
        }),
      })
    })

    await waitForApp(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heavy_rain').click()
    await page.getByTestId('simulator-run-btn').click()

    // Pipeline view should appear
    const modal = page.getByTestId('simulator-modal')
    await expect(modal.getByText('Pipeline đang chạy')).toBeVisible()
    // All 7 steps rendered — scope to modal to avoid strict-mode matches in SVG/KPI elsewhere
    for (const step of ['Traffic', 'Environment', 'Event', 'Citizen', 'Knowledge', 'Decision', 'Explanation']) {
      await expect(modal.getByText(step, { exact: true }).first()).toBeVisible()
    }
  })
})
