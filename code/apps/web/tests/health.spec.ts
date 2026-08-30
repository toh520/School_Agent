import { expect, test } from '@playwright/test'

test('shows the complete foundation health chain', async ({ page }) => {
  await page.route('**/api/v1/health/system', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          status: 'UP',
          coreService: { status: 'UP', version: '0.1.0' },
          agentService: { status: 'UP', version: '0.1.0' },
          database: { status: 'UP', version: 'PostgreSQL 16 / pgvector 0.8.3' },
        },
        error: null,
        requestId: 'playwright-request-id',
        timestamp: '2026-08-30T12:00:00+08:00',
      }),
    })
  })

  await page.goto('/')

  await expect(page.getByTestId('health-summary')).toContainText('基础链路正常')
  await expect(page.getByTestId('health-summary')).toContainText('playwright-request-id')
})

test('shows a recoverable error when the core service is unavailable', async ({ page }) => {
  await page.route('**/api/v1/health/system', (route) => route.abort('connectionrefused'))

  await page.goto('/')

  await expect(page.getByRole('alert')).toContainText('无法连接核心服务')
  await expect(page.getByRole('button', { name: '重新检查' })).toBeVisible()
})
