/**
 * Suite 1 – Layout & Static Rendering
 * API is mocked (no backend required).
 * Validates that the Mission Control shell loads and renders correctly.
 */
import { test, expect } from '@playwright/test'
import { waitForApp } from './helpers'

test.describe('Mission Control layout', () => {
  test('renders the app header with title', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByText('CityOS Mission Control')).toBeVisible()
    await expect(page.getByText('Hanoi · AI Operations Center')).toBeVisible()
  })

  test('shows left Agent Graph / Monitor tabs', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByRole('button', { name: 'Agent Graph' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Monitor' })).toBeVisible()
  })

  test('shows center digital twin map SVG', async ({ page }) => {
    await waitForApp(page)
    await expect(page.locator('text=HANOI • DIGITAL TWIN')).toBeVisible()
  })

  test('shows right AI Copilot panel', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByText('AI Copilot')).toBeVisible()
    await expect(page.getByText('Decision Report')).toBeVisible()
  })

  test('connection status badge is visible', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByTestId('connection-status')).toBeVisible()
  })

  test('chat input and send button are rendered', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByTestId('chat-input')).toBeVisible()
    await expect(page.getByTestId('chat-send')).toBeVisible()
  })

  test('simulator button is visible', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByTestId('simulator-btn')).toBeVisible()
  })

  test('KPI cards appear after mock scores load', async ({ page }) => {
    await waitForApp(page)
    await expect(page.getByText('City Health')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByText('Districts')).toBeVisible()
  })

  test('switches left panel from Agent Graph to Monitor', async ({ page }) => {
    await waitForApp(page)
    await page.getByRole('button', { name: 'Monitor' }).click()
    await expect(page.getByText('Supervisor')).toBeVisible()
    await page.getByRole('button', { name: 'Agent Graph' }).click()
    await expect(page.getByRole('button', { name: 'Agent Graph' })).toBeVisible()
  })
})
