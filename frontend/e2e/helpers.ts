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

/** Registers API mocks so tests run without a backend, then navigates to app. */
export async function waitForApp(page: Page) {
  await page.route('**/api/districts', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DISTRICTS) })
  )
  await page.route('**/api/scores', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SCORES) })
  )
  // Let WebSocket fail silently (no backend) — doesn't block UI
  await page.goto('/')
  await expect(page.getByTestId('app-header')).toBeVisible({ timeout: 15_000 })
  // Wait for TanStack Query to resolve the mocked districts (district 1 = Hoàn Kiếm selected by default)
  await expect(page.getByText('Hoàn Kiếm', { exact: false }).first()).toBeVisible({ timeout: 8_000 })
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

export { MOCK_DISTRICTS }
