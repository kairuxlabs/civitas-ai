/**
 * Suite 6 – Decision Workspace (Stitch / formerly Mission Control v2)
 * All /api/v2/* calls mocked; no backend required.
 */
import { test, expect } from '@playwright/test'
import { waitForApp, switchToMissionControl } from './helpers'

test.describe('Decision Workspace', () => {
  test('opening workspace shows the goal input', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)
    await expect(page.getByRole('heading', { name: 'Decision Workspace' })).toBeVisible()
    await expect(page.getByRole('button', { name: /Execute Decision/i })).toBeVisible()
  })

  test('submitting a goal shows the active run', async ({ page }) => {
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
    await page.route('**/api/v2/runs/run-1', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(runningRun),
    }))

    await page.getByPlaceholder(/Reduce congestion/i).fill('Test goal')
    await page.getByRole('button', { name: /Execute Decision/i }).click()

    await expect(page.getByText('Active run: run-1')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByRole('heading', { name: 'Test goal' })).toBeVisible()
  })

  test('an awaiting_approval run shows Approve/Reject buttons that call the resolve endpoint', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)

    const runningRun = {
      run_id: 'run-2', goal: 'Respond to pollution', district_id: 1, status: 'awaiting_approval',
      tasks: [],
      decision: {
        summary: 'High pollution', prediction: 'AQI rising', risk: 'high',
        recommendation: ['Issue health advisory'], confidence: 55, evidence: [],
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

    await page.getByPlaceholder(/Reduce congestion/i).fill('Respond to pollution')
    await page.getByRole('button', { name: /Execute Decision/i }).click()

    await expect(page.getByRole('button', { name: /Approve/i })).toBeVisible({ timeout: 8_000 })
    await page.getByRole('button', { name: /Approve/i }).click()

    await expect.poll(() => resolveBody).toEqual({ approved: true })
  })

  test('run history sidebar lists a submitted goal', async ({ page }) => {
    await waitForApp(page)
    await switchToMissionControl(page)

    await page.route('**/api/v2/goal', route => route.fulfill({
      status: 202, contentType: 'application/json',
      body: JSON.stringify({
        run_id: 'run-3', goal: 'History test', district_id: 1, status: 'done',
        tasks: [], decision: null, workflow_steps: [], timeline: [],
        created_at: new Date().toISOString(), decision_record_id: null, reflection: null,
      }),
    }))
    await page.route('**/api/v2/runs/run-3', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify({
        run_id: 'run-3', goal: 'History test', district_id: 1, status: 'done',
        tasks: [], decision: null, workflow_steps: [], timeline: [],
        created_at: new Date().toISOString(), decision_record_id: null, reflection: null,
      }),
    }))
    await page.route('**/api/v2/runs', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        runs: [{ run_id: 'run-3', goal: 'History test', district_id: 1, status: 'done', created_at: new Date().toISOString(), task_count: 0, confidence: 90 }],
      }),
    }))

    await page.getByPlaceholder(/Reduce congestion/i).fill('History test')
    await page.getByRole('button', { name: /Execute Decision/i }).click()

    await expect(page.getByRole('button', { name: /History test/ })).toBeVisible({ timeout: 8_000 })
  })

  // SimulationPanel / Digital Twin controls live on the legacy MissionControlPage,
  // which is no longer routed in the Stitch shell (Workspace replaces it for phase 1).
  test.skip('Digital Twin panel Start button is visible and starts the simulation', async () => {})

  test('Decision Sessions page renders a session card from the API', async ({ page }) => {
    await waitForApp(page)

    await page.route('**/api/decision-sessions', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1, run_id: 'run-9', goal: 'Reduce congestion at Hoan Kiem', district_id: 1,
          status: 'observing', decision_id: 5,
          baseline_scores: { traffic_score: 60, environment_score: 70, citizen_score: 65, risk_score: 20, overall_score: 68 },
          expected_outcome: null, observed_scores: null, outcome_delta: null,
          success_rate: null, outcome_status: null, context_snapshot: null, outcome_evidence: null,
          created_at: new Date().toISOString(), approved_at: new Date().toISOString(),
          observed_at: null, evaluated_at: null,
        },
      ]),
    }))
    await page.route('**/api/decision-sessions/analytics', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        total_sessions: 1, approval_rate: 100, evaluated_count: 0,
        improved_rate: null, avg_improvement: null, avg_decision_latency_minutes: 4,
      }),
    }))

    await page.goto('/sessions')
    await expect(page.getByTestId('decision-sessions-page')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByTestId('decision-session-card')).toBeVisible({ timeout: 8_000 })
    await expect(page.getByText('Reduce congestion at Hoan Kiem')).toBeVisible()
  })
})
