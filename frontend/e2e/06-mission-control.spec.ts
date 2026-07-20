/**
 * Suite 6 – Mission Control v2 (Autonomous Runtime)
 * First e2e coverage for MissionControlPage — previously untested.
 * All /api/v2/* calls mocked; no backend required.
 */
import { test, expect } from '@playwright/test'
import { waitForApp, switchToMissionControl } from './helpers'

test.describe('Mission Control v2', () => {
  test('switching to Mission Control v2 shows the goal input', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)
    await expect(page.getByText('Giao mục tiêu cho CityOS Runtime')).toBeVisible()
  })

  test('submitting a goal shows the run status', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)
    const runningRun = {
      run_id: 'run-1', goal: 'Test goal', district_id: 1, status: 'running',
      tasks: [], decision: null, workflow_steps: [], timeline: [],
      created_at: new Date().toISOString(), decision_record_id: null, reflection: null,
    }
    await page.route('**/api/v2/goal', route => route.fulfill({
      status: 202, contentType: 'application/json', body: JSON.stringify(runningRun),
    }))
    // MissionControlPage sets activeRunId on submit success and immediately fetches
    // GET /api/v2/runs/run-1 via useQuery — must be mocked or the status never renders.
    await page.route('**/api/v2/runs/run-1', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(runningRun),
    }))

    await page.getByPlaceholder(/Chuẩn bị thành phố/).fill('Test goal')
    await page.getByRole('button', { name: /Thực thi/ }).click()

    await expect(page.getByText('Đang thực thi')).toBeVisible({ timeout: 8_000 })
  })

  test('an awaiting_approval run shows Approve/Reject buttons that call the resolve endpoint', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)

    const runningRun = {
      run_id: 'run-2', goal: 'Ứng phó ô nhiễm', district_id: 1, status: 'awaiting_approval',
      tasks: [],
      decision: {
        summary: 'Ô nhiễm cao', prediction: 'AQI tăng', risk: 'high',
        recommendation: ['Cảnh báo sức khỏe'], confidence: 55, evidence: [],
      },
      workflow_steps: [], timeline: [], created_at: new Date().toISOString(),
      decision_record_id: 9, reflection: null,
    }
    await page.route('**/api/v2/goal', route => route.fulfill({ status: 202, contentType: 'application/json', body: JSON.stringify(runningRun) }))
    await page.route('**/api/v2/runs/run-2', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(runningRun) }))

    let resolveBody: unknown = null
    await page.route('**/api/v2/runs/run-2/approval', async route => {
      resolveBody = route.request().postDataJSON()
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...runningRun, status: 'executing_workflow' }) })
    })

    await page.getByPlaceholder(/Chuẩn bị thành phố/).fill('Ứng phó ô nhiễm')
    await page.getByRole('button', { name: /Thực thi/ }).click()

    await expect(page.getByRole('button', { name: /Phê duyệt/ })).toBeVisible({ timeout: 8_000 })
    await page.getByRole('button', { name: /Phê duyệt/ }).click()

    await expect.poll(() => resolveBody).toEqual({ approved: true })
  })

  test('run history sidebar lists a submitted goal', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)

    await page.route('**/api/v2/goal', route => route.fulfill({
      status: 202, contentType: 'application/json',
      body: JSON.stringify({
        run_id: 'run-3', goal: 'Lịch sử test', district_id: 1, status: 'done',
        tasks: [], decision: null, workflow_steps: [], timeline: [],
        created_at: new Date().toISOString(), decision_record_id: null, reflection: null,
      }),
    }))
    await page.route('**/api/v2/runs', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        runs: [{ run_id: 'run-3', goal: 'Lịch sử test', district_id: 1, status: 'done', created_at: new Date().toISOString(), task_count: 0, confidence: 90 }],
      }),
    }))

    await page.getByPlaceholder(/Chuẩn bị thành phố/).fill('Lịch sử test')
    await page.getByRole('button', { name: /Thực thi/ }).click()

    await expect(page.getByText('Lịch sử test')).toBeVisible({ timeout: 8_000 })
  })

  test('Digital Twin panel Start button is visible and starts the simulation', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)

    await page.route('**/api/v2/simulation/start', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        running: true, scenario: 'heavy_rain', scenario_label: 'Mưa lớn', interval_s: 30, auto_goal: true, tick: 0,
        values: { rain: 10, aqi: 90, temperature: 28, humidity: 75, wind_speed: 12 }, last_auto_goal: null,
      }),
    }))

    await expect(page.getByRole('button', { name: /Bắt đầu/ })).toBeVisible()
    await page.getByRole('button', { name: /Bắt đầu/ }).click()

    await expect(page.getByRole('button', { name: /Dừng/ })).toBeVisible({ timeout: 8_000 })
  })
})
