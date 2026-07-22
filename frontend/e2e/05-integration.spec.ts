/**
 * Suite 5 – Full Integration (requires backend + frontend both running)
 * Skip automatically if backend is not reachable.
 * Tests real HTTP flow end-to-end against the live backend.
 */
import { test, expect } from '@playwright/test'
import { backendReachable } from './helpers'

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
})
