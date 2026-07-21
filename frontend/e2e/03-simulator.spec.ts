/**
 * Suite 3 – Simulator Modal UI
 * Does NOT require the backend. Tests the modal open/close/select flow
 * and mocks the /api/simulate endpoint so the pipeline progress is testable.
 */
import { test, expect } from '@playwright/test'
import { waitForCommandCenter } from './helpers'

test.describe('Simulator modal', () => {
  test('opens when clicking Mô phỏng button', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-modal')).toBeVisible()
    await expect(page.getByText('What-If Simulator')).toBeVisible()
  })

  test('closes when clicking X button', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-modal')).toBeVisible()
    await page.locator('[data-testid="simulator-modal"] button').filter({ hasText: '' }).first().click()
    await expect(page.getByTestId('simulator-modal')).not.toBeVisible()
  })

  test('shows 4 scenario cards', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('scenario-heavy_rain')).toBeVisible()
    await expect(page.getByTestId('scenario-air_pollution')).toBeVisible()
    await expect(page.getByTestId('scenario-major_event')).toBeVisible()
    await expect(page.getByTestId('scenario-heatwave')).toBeVisible()
  })

  test('Run button is disabled before selecting a scenario', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await expect(page.getByTestId('simulator-run-btn')).toBeDisabled()
  })

  test('Run button enables after selecting a scenario', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heavy_rain').click()
    await expect(page.getByTestId('simulator-run-btn')).toBeEnabled()
  })

  test('selecting different scenario changes active card', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heatwave').click()
    // Heatwave card should have scale-[1.02] applied (selected state)
    const card = page.getByTestId('scenario-heatwave')
    await expect(card).toHaveClass(/border-red-500/)
  })

  test('shows the before/after comparison after clicking Run (with mocked API)', async ({ page }) => {
    // Mock both endpoints — CommandCenterPage now runs a baseline /api/chat call
    // before /api/simulate, and with both mocked (no real backend/pipeline), the
    // flow can reach the final "done" comparison view before any transient
    // pipeline-progress text is reliably observable, so this test asserts on
    // the final Before/After content rather than the mid-flight step tracker.
    await page.route('**/api/chat', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          prediction: { flood_risk: 'low' },
          impact: {},
          recommendations: ['Theo dõi thời tiết'],
          confidence: 70,
          explanation: ['Baseline status.'],
          evidence: [],
        }),
      })
    })
    await page.route('**/api/simulate', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          prediction: { flood_risk: 'high' },
          impact: { traffic: 'severe' },
          recommendations: ['Theo dõi thời tiết', 'Evacuate low areas'],
          confidence: 88,
          explanation: ['Heavy rain detected', 'Flood risk elevated'],
          evidence: [],
        }),
      })
    })

    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-heavy_rain').click()
    await page.getByTestId('simulator-run-btn').click()

    const modal = page.getByTestId('simulator-modal')
    await expect(modal.getByText('✓ So sánh Before/After')).toBeVisible({ timeout: 10_000 })
    await expect(modal.getByText('70%')).toBeVisible()
    await expect(modal.getByText('88%')).toBeVisible()
    await expect(modal.getByText(/Evacuate low areas/)).toBeVisible()
    await expect(modal.getByText(/\(mới\)/)).toBeVisible()
  })
})
