import { expect, test } from '@playwright/test'

test('shows the login page without exposing infrastructure status', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: /智慧校园.*伴你学习与生活/ })).toBeVisible()
  await expect(page.getByRole('button', { name: '登录', exact: true })).toBeVisible()
  await expect(page.getByText('基础服务运行正常')).toHaveCount(0)
  await expect(page.getByText('基础服务暂不可用')).toHaveCount(0)
})

test('keeps login errors recoverable when the core service is unavailable', async ({ page }) => {
  await page.route('**/api/v1/auth/login', (route) => route.abort('connectionrefused'))
  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('invalid-password')
  await page.getByRole('button', { name: '登录', exact: true }).click()

  await expect(page.getByRole('alert')).toContainText('登录失败，请检查账号和密码')
  await expect(page.getByRole('button', { name: '登录', exact: true })).toBeVisible()
})
