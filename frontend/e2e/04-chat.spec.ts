/**
 * Suite 4 – AI Copilot Chat
 * Mocks /api/chat so tests run without a live backend.
 */
import { test, expect } from '@playwright/test'
import { waitForCommandCenter } from './helpers'

const MOCK_DECISION = {
  prediction: { flood_risk: 'medium', traffic: 'moderate' },
  impact: { citizens_affected: '50,000' },
  recommendations: ['Deploy traffic officers', 'Issue advisory'],
  confidence: 82,
  explanation: [
    'Current AQI is within normal limits.',
    'No active flood warnings for this district.',
    'Recommend standard monitoring protocols.',
  ],
  evidence: [
    { id: 'ev-1', agent: 'traffic', source: 'OpenAQ', type: 'sensor', content: 'AQI 90 (moderate)', confidence: 0.9, time: '2026-07-20T08:00:00Z' },
    { id: 'ev-2', agent: 'environment', source: 'OpenAQ', type: 'sensor', content: 'AQI 90 (MODERATE)', confidence: 0.9, time: '2026-07-20T08:00:00Z' },
  ],
}

test.describe('AI Copilot chat', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/chat', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_DECISION),
      })
    })
    await waitForCommandCenter(page)
  })

  test('chat input accepts text', async ({ page }) => {
    await page.getByTestId('chat-input').fill('What is the AQI?')
    await expect(page.getByTestId('chat-input')).toHaveValue('What is the AQI?')
  })

  test('send button disabled when input is empty', async ({ page }) => {
    await expect(page.getByTestId('chat-send')).toBeDisabled()
  })

  test('send button enabled when input has text', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Any events today?')
    await expect(page.getByTestId('chat-send')).toBeEnabled()
  })

  test('pressing Enter sends message and shows user bubble', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Traffic status?')
    await page.keyboard.press('Enter')
    await expect(page.getByTestId('chat-messages').getByText('Traffic status?')).toBeVisible()
  })

  test('AI response appears after send', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Flood risk?')
    await page.getByTestId('chat-send').click()
    // Last explanation string
    await expect(
      page.getByTestId('chat-messages').getByText('Recommend standard monitoring protocols.')
    ).toBeVisible({ timeout: 10_000 })
  })

  test('Decision Report panel updates with confidence after chat', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Status?')
    await page.keyboard.press('Enter')
    // Confidence 82% should appear in the Decision Report
    await expect(page.getByText('82%', { exact: false })).toBeVisible({ timeout: 10_000 })
  })

  test('clicking Send clears the input field', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Clear me?')
    await page.getByTestId('chat-send').click()
    await expect(page.getByTestId('chat-input')).toHaveValue('')
  })

  test('clicking a recommendation opens the evidence modal', async ({ page }) => {
    await page.getByTestId('chat-input').fill('Status?')
    await page.keyboard.press('Enter')
    await expect(
      page.getByTestId('chat-messages').getByText('Recommend standard monitoring protocols.')
    ).toBeVisible({ timeout: 10_000 })
    await page.getByTestId('recommendation-item').first().click()
    await expect(page.getByTestId('evidence-modal')).toBeVisible()
    // exact: true — the mock's two evidence items differ only by case
    // ("moderate" vs "MODERATE"), and Playwright's getByText is
    // case-insensitive by default, which would otherwise match both.
    await expect(page.getByText('AQI 90 (moderate)', { exact: true })).toBeVisible()
  })
})
