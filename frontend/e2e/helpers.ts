import { type Page, expect } from '@playwright/test'

const MOCK_DISTRICTS = [
  { id: 1,  city_id: 'hanoi', name: 'Hoàn Kiếm' },
  { id: 2,  city_id: 'hanoi', name: 'Ba Đình' },
  { id: 3,  city_id: 'hanoi', name: 'Đống Đa' },
  { id: 4,  city_id: 'hanoi', name: 'Hai Bà Trưng' },
  { id: 5,  city_id: 'hanoi', name: 'Hoàng Mai' },
  { id: 6,  city_id: 'hanoi', name: 'Thanh Xuân' },
  { id: 7,  city_id: 'hanoi', name: 'Cầu Giấy' },
  { id: 8,  city_id: 'hanoi', name: 'Long Biên' },
  { id: 9,  city_id: 'hanoi', name: 'Nam Từ Liêm' },
  { id: 10, city_id: 'hanoi', name: 'Bắc Từ Liêm' },
  { id: 11, city_id: 'hanoi', name: 'Tây Hồ' },
  { id: 12, city_id: 'hanoi', name: 'Hà Đông' },
]

const MOCK_SCORES = MOCK_DISTRICTS.map((d, i) => ({
  id: d.id,
  city_id: 'hanoi',
  district_id: d.id,
  timestamp: new Date().toISOString(),
  traffic_score: 70 + i,
  environment_score: 65 + i,
  citizen_score: 70,
  risk_score: 25 - i,
  overall_score: 72 + i,
}))

/** Registers API mocks so tests run without a backend, then navigates to Overview. */
export async function waitForApp(page: Page) {
  await page.route('**/api/districts', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DISTRICTS) })
  )
  await page.route('**/api/scores', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SCORES) })
  )
  await page.route('**/health', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  )
  await page.route('**/api/decision-sessions', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  )
  await page.route('**/api/decision-sessions/analytics', route =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        total_sessions: 0, approval_rate: null, evaluated_count: 0,
        improved_rate: null, avg_improvement: null, avg_decision_latency_minutes: null,
      }),
    })
  )
  await page.goto('/')
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('overview-page')).toBeVisible({ timeout: 8_000 })
}

/**
 * Overview mocks + navigate to Command Center (chat / map / simulator live here, not on `/`).
 */
export async function waitForCommandCenter(page: Page) {
  await waitForApp(page)
  await page.goto('/command-center')
  await expect(page.getByTestId('command-center-route')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('app-header')).toBeVisible({ timeout: 15_000 })
}

/** Returns true if backend is reachable. */
export async function backendReachable(page: Page): Promise<boolean> {
  try {
    const resp = await page.request.get('http://localhost:8000/health')
    return resp.ok()
  } catch {
    return false
  }
}

/** Registers v2 API mocks and opens the Stitch Decision Workspace at `/workspace`. */
export async function switchToMissionControl(page: Page) {
  await page.route('**/api/v2/runs', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ runs: [] }) })
  )
  await page.route('**/api/v2/monitor', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ agents: {}, active_runs: 0, total_runs: 0 }) })
  )
  await page.route('**/api/v2/simulation/scenarios', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ scenarios: [{ name: 'heavy_rain', label: 'Heavy rain' }] }) })
  )
  await page.route('**/api/v2/simulation/status', route =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        running: false, scenario: 'normal', scenario_label: 'Normal', interval_s: 30, auto_goal: true, tick: 0,
        values: { rain: 0, aqi: 90, temperature: 30, humidity: 70, wind_speed: 10 }, last_auto_goal: null,
      }),
    })
  )
  await page.goto('/workspace')
  await expect(page.getByTestId('decision-workspace-page')).toBeVisible({ timeout: 8_000 })
  await expect(page.getByPlaceholder(/Reduce congestion/i)).toBeVisible()
}

export { MOCK_DISTRICTS }
