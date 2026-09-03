import { expect, test } from '@playwright/test'

const conversationId = '30000000-0000-0000-0000-000000000001'
const taskId = '31000000-0000-0000-0000-000000000001'
const resultId = '32000000-0000-0000-0000-000000000001'

const me = {
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
    updatedAt: '2026-09-01T00:00:00Z',
  },
  preference: {
    tastes: [],
    budget: null,
    avoidances: [],
    allergens: [],
    dietaryGoal: null,
    updatedAt: '2026-09-01T00:00:00Z',
  },
  authorizations: Object.fromEntries(
    ['EXAMS', 'MASTERY', 'DIET', 'CHAT_HISTORY'].map((scope) => [
      scope,
      { scope, granted: false, changedAt: '2026-09-01T00:00:00Z' },
    ]),
  ),
}

test.beforeEach(async ({ page }) => {
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
            id: me.profile.id,
            username: 'student1',
            role: 'STUDENT',
            nickname: '学生用户一',
          },
        },
        error: null,
        requestId: 'login',
        timestamp: '2026-09-01T00:00:00Z',
      },
    }),
  )
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: me,
        error: null,
        requestId: 'me',
        timestamp: '2026-09-01T00:00:00Z',
      },
    }),
  )
})

test('student completes a streamed Agent turn and records feedback', async ({ page }) => {
  let completed = false
  let feedback = ''
  await page.route('**/agent-api/v1/conversations', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: [
          {
            id: conversationId,
            title: completed ? '学校奖学金申请需要什么材料？' : '新会话',
            currentIntent: completed ? 'CAMPUS_QA' : null,
            updatedAt: '2026-09-01T00:00:00Z',
          },
        ],
        error: null,
        requestId: 'list',
        timestamp: '2026-09-01T00:00:00Z',
      },
    }),
  )
  await page.route(`**/agent-api/v1/conversations/${conversationId}`, (route) =>
    route.fulfill({
      json: {
        success: true,
        data: {
          id: conversationId,
          title: completed ? '学校奖学金申请需要什么材料？' : '新会话',
          currentIntent: completed ? 'CAMPUS_QA' : null,
          updatedAt: '2026-09-01T00:00:00Z',
          messages: completed
            ? [
                {
                  id: 'message-user',
                  role: 'USER',
                  content: '学校奖学金申请需要什么材料？',
                  sequenceNumber: 1,
                  resultVersionId: null,
                  taskId: null,
                  intent: null,
                  fallbackUsed: false,
                  basis: [],
                  limitations: [],
                  createdAt: '2026-09-01T00:00:00Z',
                },
                {
                  id: 'message-assistant',
                  role: 'ASSISTANT',
                  content: '已识别校园知识问答需求，并保留当前条件。',
                  sequenceNumber: 2,
                  resultVersionId: resultId,
                  taskId,
                  intent: 'CAMPUS_QA',
                  fallbackUsed: false,
                  basis: ['当前会话内容', '受控工具校验结果'],
                  limitations: [],
                  createdAt: '2026-09-01T00:00:01Z',
                },
              ]
            : [],
        },
        error: null,
        requestId: 'detail',
        timestamp: '2026-09-01T00:00:00Z',
      },
    }),
  )
  await page.route(`**/agent-api/v1/conversations/${conversationId}/messages`, async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      content: '学校奖学金申请需要什么材料？',
    })
    completed = true
    await route.fulfill({
      contentType: 'text/event-stream',
      body: [
        'event: status\ndata: {"phase":"UNDERSTANDING","label":"正在理解你的需求"}\n\n',
        'event: intent\ndata: {"intent":"CAMPUS_QA"}\n\n',
        'event: tool\ndata: {"name":"context_snapshot","status":"SUCCESS","durationMs":1}\n\n',
        'event: content\ndata: {"delta":"已识别校园知识问答需求，"}\n\n',
        'event: content\ndata: {"delta":"并保留当前条件。"}\n\n',
        `event: done\ndata: ${JSON.stringify({
          taskId,
          messageId: 'message-assistant',
          resultVersionId: resultId,
          result: {
            intent: 'CAMPUS_QA',
            status: 'COMPLETED',
            missingFields: [],
            content: '已识别校园知识问答需求，并保留当前条件。',
            structuredResult: {},
            basis: ['当前会话内容', '受控工具校验结果'],
            limitations: [],
            modelName: 'Qwen/Qwen3-8B',
            fallbackUsed: false,
          },
        })}\n\n`,
      ].join(''),
    })
  })
  await page.route(`**/agent-api/v1/results/${resultId}/feedback`, async (route) => {
    feedback = route.request().postDataJSON().category
    await route.fulfill({ json: { success: true, data: { saved: true } } })
  })

  await loginAndOpenAgent(page)
  await expect(page.getByText('最近安全记录')).toHaveCount(0)
  await page.getByRole('button', { name: '学校奖学金申请需要什么材料？' }).click()
  await page.getByRole('button', { name: '发送问题' }).click()

  await expect(page.getByText('已识别校园知识问答需求，并保留当前条件。')).toBeVisible()
  await expect(page.locator('.knowledge-stamp')).toHaveText('校内知识库')
  await expect(page.getByText(/依据：当前会话内容/)).toBeVisible()
  await page.getByRole('button', { name: '有帮助' }).click()
  expect(feedback).toBe('HELPFUL')
  await expect(page.getByRole('button', { name: '内容错误' })).toBeVisible()
  await expect(page.getByRole('button', { name: '信息过期' })).toBeVisible()
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.locator('.knowledge-scope')).toBeVisible()
})

test('stream failure keeps the composer recoverable', async ({ page }) => {
  await page.route('**/agent-api/v1/conversations', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: [{ id: conversationId, title: '新会话', currentIntent: null, updatedAt: '' }],
      },
    }),
  )
  await page.route(`**/agent-api/v1/conversations/${conversationId}`, (route) =>
    route.fulfill({
      json: {
        success: true,
        data: {
          id: conversationId,
          title: '新会话',
          currentIntent: null,
          updatedAt: '',
          messages: [],
        },
      },
    }),
  )
  await page.route(`**/agent-api/v1/conversations/${conversationId}/messages`, (route) =>
    route.fulfill({
      status: 503,
      json: { success: false, error: { code: 'MODEL_UNAVAILABLE', message: '模型暂时不可用' } },
    }),
  )

  await loginAndOpenAgent(page)
  await page.getByLabel('向校园助手提问').fill('帮我看看')
  await page.getByRole('button', { name: '发送问题' }).click()

  await expect(page.getByText('模型暂时不可用')).toBeVisible()
  await page.getByLabel('向校园助手提问').fill('重新发送')
  await expect(page.getByRole('button', { name: '发送问题' })).toBeEnabled()
})

async function loginAndOpenAgent(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('Student@123')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('link', { name: '校园助手', exact: true }).click()
  await expect(page.getByRole('region', { name: '校园知识助手' })).toBeVisible()
}
