import { expect, test } from '@playwright/test'

test('Java reports the complete live service chain while login stays business-focused', async ({
  page,
  request,
}) => {
  const response = await request.get('http://127.0.0.1:8080/api/v1/health/system')
  expect(response.status()).toBe(200)
  const body = await response.json()
  expect(body.data.status).toBe('UP')
  expect(body.data.coreService.status).toBe('UP')
  expect(body.data.agentService.status).toBe('UP')
  expect(body.data.database.status).toBe('UP')

  await page.goto('/')
  await expect(page.getByRole('heading', { name: /智慧校园.*伴你学习与生活/ })).toBeVisible()
  await expect(page.getByText('基础服务运行正常')).toHaveCount(0)
})
