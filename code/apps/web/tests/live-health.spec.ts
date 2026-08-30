import { expect, test } from '@playwright/test'

test('browser reaches Java, Python and PostgreSQL through the live health page', async ({
  page,
}) => {
  await page.goto('/')

  const summary = page.getByTestId('health-summary')
  await expect(summary).toContainText('基础链路正常')
  await expect(summary).toContainText('Java 核心服务')
  await expect(summary).toContainText('Python Agent 服务')
  await expect(summary).toContainText('PostgreSQL / pgvector')
})
