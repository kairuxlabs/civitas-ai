/**
 * Suite 5 – Full Integration (requires backend + frontend both running)
 * Skip automatically if backend is not reachable.
 * Tests real HTTP + WebSocket flow end-to-end.
 */
import { test, expect } from '@playwright/test'
import { waitForCommandCenter, backendReachable } from './helpers'

test.describe('Full stack integration', () => {
  test.beforeEach(async ({ page }) => {
    const alive = await backendReachable(page)
    test.skip(!alive, 'Backend not running — skipping integration tests')
  })

  test('health endpoint returns ok', async ({ page }) => {
    const resp = await page.request.get('http://localhost:8000/health')
    expect(resp.ok()).toBe(true)
    const body = await resp.json()
    expect(body.status).toBe('ok')
  })

  test('districts API returns 12 Hanoi districts', async ({ page }) => {
    const resp = await page.request.get('http://localhost:8000/api/districts')
    expect(resp.ok()).toBe(true)
    const districts = await resp.json()
    expect(districts.length).toBe(12)
  })

  test('WebSocket connection shows Live badge', async ({ page }) => {
    await waitForCommandCenter(page)
    // Give WS time to connect
    await page.waitForTimeout(2000)
    await expect(page.getByTestId('connection-status')).toContainText('Live')
  })

  test('selecting district 1 shows Hoàn Kiếm in info bar', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.locator('[data-testid="district-1"]').click()
    await expect(page.getByText('Hoàn Kiếm')).toBeVisible()
  })

  test('KPI cards appear when scores are loaded', async ({ page }) => {
    await waitForCommandCenter(page)
    // Wait for TanStack Query to fetch scores (up to 8s)
    await expect(page.getByText('City Health')).toBeVisible({ timeout: 8000 })
    await expect(page.getByText('Districts')).toBeVisible()
  })

  test('chat sends real request and receives decision', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.locator('[data-testid="district-1"]').click()
    await page.getByTestId('chat-input').fill('What is the current flood risk?')
    await page.getByTestId('chat-send').click()
    // User bubble appears immediately
    await expect(page.getByText('What is the current flood risk?')).toBeVisible()
    // AI response within 20s (pipeline takes ~5-10s)
    await expect(page.getByTestId('chat-messages').locator('.rounded-xl').last())
      .not.toBeEmpty({ timeout: 20_000 })
    // Decision Report should have confidence value
    await expect(page.getByText('%', { exact: false })).toBeVisible({ timeout: 20_000 })
  })

  test('simulator sends real request and shows pipeline progress', async ({ page }) => {
    await waitForCommandCenter(page)
    await page.getByTestId('simulator-btn').click()
    await page.getByTestId('scenario-air_pollution').click()
    await page.getByTestId('simulator-run-btn').click()

    // Pipeline view appears
    await expect(page.getByText('Pipeline đang chạy')).toBeVisible()

    // Wait for pipeline_done (max 25s)
    await expect(page.getByText('Mô phỏng hoàn thành')).toBeVisible({ timeout: 25_000 })
  })
})
