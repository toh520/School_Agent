import { expect, test } from '@playwright/test'

const meData = {
  profile: {
    id: '10000000-0000-0000-0000-000000000001',
    username: 'student1',
    studentNumber: '2026000001',
    realName: '学生用户一',
    phone: '13900000001',
    role: 'STUDENT',
    nickname: '学生用户一',
    avatarUrl: null,
    contact: null,
    updatedAt: '2026-08-30T12:00:00Z',
  },
  preference: {
    tastes: [],
    budget: null,
    avoidances: [],
    allergens: [],
    dietaryGoal: null,
    updatedAt: '2026-08-30T12:00:00Z',
  },
  authorizations: Object.fromEntries(
    ['EXAMS', 'MASTERY', 'DIET', 'CHAT_HISTORY'].map((scope) => [
      scope,
      { scope, granted: false, changedAt: '2026-08-30T12:00:00Z' },
    ]),
  ),
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/health/system', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: { status: 'UP' },
        error: null,
        requestId: 'id',
        timestamp: '2026-08-30T12:00:00Z',
      },
    }),
  )
})

test('student logs in and sees default-deny authorization controls', async ({ page }) => {
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: {
          accessToken: 'access',
          refreshToken: 'refresh',
          tokenType: 'Bearer',
          expiresIn: 900,
          user: {
            id: meData.profile.id,
            username: 'student1',
            role: 'STUDENT',
            nickname: '学生用户一',
          },
        },
        error: null,
        requestId: 'login',
        timestamp: '2026-08-30T12:00:00Z',
      },
    }),
  )
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: meData,
        error: null,
        requestId: 'me',
        timestamp: '2026-08-30T12:00:00Z',
      },
    }),
  )

  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('Student@123')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByText('学生用户一').first()).toBeVisible()
  await page.getByRole('button', { name: '数据授权' }).click()
  await expect(page.getByText('四类数据默认不授权')).toBeVisible()
  await expect(page.getByRole('switch', { name: '考试数据' })).not.toBeChecked()
  await expect(page.getByRole('switch', { name: '饮食与过敏信息' })).not.toBeChecked()
})

test('invalid credentials show a clear error without leaving login page', async ({ page }) => {
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      status: 401,
      json: {
        success: false,
        data: null,
        error: { code: 'INVALID_CREDENTIALS', message: '账号或密码错误' },
        requestId: 'failed',
        timestamp: '2026-08-30T12:00:00Z',
      },
    }),
  )
  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('wrong')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('账号或密码错误')
})

test('student registers with verified identity fields and enters personal center', async ({
  page,
}) => {
  await page.route('**/api/v1/auth/register', async (route) => {
    const payload = route.request().postDataJSON()
    expect(payload).toMatchObject({
      studentNumber: '2026000088',
      phone: '13900000088',
      realName: '测试学生',
      username: 'student_88',
    })
    await route.fulfill({
      json: {
        success: true,
        data: {
          accessToken: 'access',
          refreshToken: 'refresh',
          tokenType: 'Bearer',
          expiresIn: 900,
          user: {
            id: meData.profile.id,
            username: 'student_88',
            role: 'STUDENT',
            nickname: '测试学生',
          },
        },
        error: null,
        requestId: 'register',
        timestamp: '2026-08-31T12:00:00Z',
      },
    })
  })
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: meData,
        error: null,
        requestId: 'me',
        timestamp: '2026-08-31T12:00:00Z',
      },
    }),
  )

  await page.goto('/')
  await page.getByRole('tab', { name: '注册' }).click()
  await page.getByLabel('学号').fill('2026000088')
  await page.getByLabel('姓名').fill('测试学生')
  await page.getByLabel('手机号').fill('13900000088')
  await page.getByLabel('登录账号').fill('student_88')
  await page.getByLabel('设置密码').fill('Password@88')
  await page.getByLabel('确认密码').fill('Password@88')
  await page.getByRole('button', { name: '创建账号' }).click()

  await expect(page.getByText('学生用户一').first()).toBeVisible()
  await expect(page.getByText('2026000001')).toBeVisible()
})
