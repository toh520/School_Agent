import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const userId = '10000000-0000-0000-0000-000000000001'

const me = {
  profile: {
    id: userId,
    username: 'student1',
    studentNumber: '2026000001',
    realName: '学生用户一',
    phone: '13900000001',
    role: 'STUDENT',
    nickname: '学生用户一',
    avatarUrl: null,
    contact: null,
    updatedAt: '2026-09-03T00:00:00Z',
  },
  preference: {
    tastes: [],
    budget: null,
    avoidances: [],
    allergens: [],
    dietaryGoal: null,
    updatedAt: '2026-09-03T00:00:00Z',
  },
  authorizations: Object.fromEntries(
    ['EXAMS', 'MASTERY', 'DIET', 'CHAT_HISTORY'].map((scope) => [
      scope,
      { scope, granted: true, changedAt: '2026-09-03T00:00:00Z' },
    ]),
  ),
}

function answer(overrides: Record<string, unknown> = {}) {
  return {
    mode: 'EXPLAIN',
    course: '数据结构',
    answer: '队列保证节点按进入顺序被访问。',
    steps: ['根节点先入队', '每次取出队首并将孩子入队', '队列为空时结束'],
    conclusion: '层序遍历使用先进先出队列。',
    diagnosis: [],
    correctedPoints: [],
    verification: '关键结论与课程资料一致',
    validationStatus: 'MATERIAL_SUPPORTED',
    sources: [
      {
        materialId: 'm1',
        fileName: '数据结构讲义.pdf',
        locator: '第 18 页',
        snippet: '层序遍历按层访问结点，使用队列保存待访问结点。',
      },
    ],
    limitations: [],
    prerequisiteKnowledge: ['队列的先进先出性质'],
    keyConcepts: ['访问顺序', '待访问结点'],
    keyClaims: [
      {
        text: '队列的先进先出性质保持同层结点的访问顺序',
        origin: 'COURSE_MATERIAL',
        sources: [
          {
            materialId: 'm1',
            fileName: '数据结构讲义.pdf',
            locator: '第 18 页',
            snippet: '层序遍历按层访问结点，使用队列保存待访问结点。',
          },
        ],
      },
      { text: '可以把队列想成候场区', origin: 'AI_SUPPLEMENT', sources: [] },
    ],
    workedExample: 'A 的孩子 B、C 依次入队，因此先访问 B 再访问 C。',
    commonMistakes: ['把栈误用为待访问容器'],
    memoryTip: '先到先访问。',
    selfTestQuestion: '若根为 A，孩子为 B、C，前三个访问结点是什么？',
    selfTestAnswer: 'A、B、C。',
    evidenceConflicts: [],
    ...overrides,
  }
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/auth/refresh', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: {
          accessToken: 'access',
          refreshToken: 'refresh',
          tokenType: 'Bearer',
          expiresIn: 900,
          user: { id: userId, username: 'student1', role: 'STUDENT', nickname: '学生用户一' },
        },
      },
    }),
  )
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: {
          accessToken: 'access',
          refreshToken: 'refresh',
          tokenType: 'Bearer',
          expiresIn: 900,
          user: { id: userId, username: 'student1', role: 'STUDENT', nickname: '学生用户一' },
        },
      },
    }),
  )
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({ json: { success: true, data: me, error: null } }),
  )
  await page.route('**/api/v1/exams**', (route) =>
    route.fulfill({ json: { success: true, data: [], error: null } }),
  )
  await page.route('**/api/v1/health/system', (route) =>
    route.fulfill({ json: { success: true, data: { status: 'UP' }, error: null } }),
  )
})

async function openLearning(page: Page) {
  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('Student@123')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('link', { name: '考试助手', exact: true }).click()
  await page.getByRole('button', { name: 'AI 学习工作台', exact: true }).click()
}

test('mode-specific fields, examples and learning profile are submitted', async ({ page }) => {
  let payload: Record<string, unknown> = {}
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    payload = route.request().postDataJSON()
    await route.fulfill({ json: { success: true, data: answer(), error: null } })
  })
  await openLearning(page)

  await expect(page.getByText('把一个知识点真正讲明白')).toBeVisible()
  await page.getByRole('button', { name: '深入掌握' }).click()
  await page
    .locator('.question-sheet .compact-fields .field-block')
    .nth(1)
    .locator('.el-select__wrapper')
    .click()
  await page.getByRole('option', { name: '正在复习巩固' }).click()
  await page.getByRole('button', { name: /为什么二叉树层序遍历/ }).click()
  await page.getByRole('button', { name: '生成分层讲义' }).click()

  await expect(page.getByText('一句话结论')).toBeVisible()
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '需要先知道' }).locator('span'),
  ).toHaveText('02')
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '核心概念' }).locator('span'),
  ).toHaveText('03')
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '推导步骤' }).locator('span'),
  ).toHaveText('04')
  expect(payload.learningGoal).toBe('DEEP')
  expect(payload.familiarity).toBe('REVIEW')
  expect(payload.prompt).toContain('层序遍历')

  await page.getByText('错因诊断', { exact: true }).click()
  await expect(page.getByRole('textbox', { name: '完整作答过程（必填）' })).toBeVisible()
  await expect(page.getByRole('textbox', { name: '最困惑的位置（选填）' })).toBeVisible()
})

test('visible lecture sections are renumbered when optional sections are absent', async ({
  page,
}) => {
  await page.route('**/agent-api/v1/learning/answers', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: answer({ prerequisiteKnowledge: [] }),
      },
    }),
  )
  await openLearning(page)
  await page.getByRole('textbox', { name: '知识点', exact: true }).fill('层序遍历')
  await page.getByRole('button', { name: '生成分层讲义' }).click()

  await expect(page.locator('.answer-lead-block .section-number')).toHaveText('01 · 一句话结论')
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '核心概念' }).locator('span'),
  ).toHaveText('02')
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '推导步骤' }).locator('span'),
  ).toHaveText('03')
  await expect(
    page.locator('.answer-section h3').filter({ hasText: '例题或类比' }).locator('span'),
  ).toHaveText('04')
  await expect(page.locator('.self-test .section-number')).toHaveText('06 · 自我检查')
})

test('solution reveals hints progressively and keeps final answer separate', async ({ page }) => {
  await page.route('**/agent-api/v1/learning/answers', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: answer({ mode: 'SOLVE', answer: '完整解法概述', conclusion: '后序为 DEBFCA。' }),
      },
    }),
  )
  await openLearning(page)
  await page.getByText('题目解析', { exact: true }).click()
  await page.getByRole('textbox', { name: '原题' }).fill('已知先序和中序，求后序遍历')
  await page.getByRole('button', { name: '准备分步解析' }).click()

  await expect(page.getByText('完整解法概述')).toHaveCount(0)
  await expect(page.getByText('后序为 DEBFCA。')).toHaveCount(0)
  await page.getByRole('button', { name: '给我一个提示' }).click()
  await expect(page.getByText('根节点先入队')).toBeVisible()
  await page.getByRole('button', { name: '再给一个提示' }).click()
  await expect(page.getByText('每次取出队首并将孩子入队')).toBeVisible()
  await page.getByRole('button', { name: '展开完整解法' }).click()
  await expect(page.getByText('完整解法概述')).toBeVisible()
  await expect(page.getByText('后序为 DEBFCA。')).toHaveCount(0)
  await page.getByRole('button', { name: '查看最终答案' }).click()
  await expect(page.getByText('后序为 DEBFCA。')).toBeVisible()
})

test('material evidence, AI supplement and conflict notice remain distinguishable', async ({
  page,
}) => {
  await page.route('**/agent-api/v1/learning/answers', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: answer({ evidenceConflicts: ['两份讲义对空树高度采用了不同计数口径。'] }),
      },
    }),
  )
  await openLearning(page)
  await page.getByRole('textbox', { name: '知识点', exact: true }).fill('层序遍历')
  await page.getByRole('button', { name: '生成分层讲义' }).click()

  await expect(page.getByText('课程资料支持')).toBeVisible()
  await expect(page.getByText('课程资料依据')).toBeVisible()
  await expect(page.getByText('AI 补充')).toBeVisible()
  await page.getByText('数据结构讲义.pdf · 第 18 页').click()
  await expect(page.getByText(/使用队列保存待访问结点/)).toBeVisible()
  await expect(page.getByText(/不同计数口径/)).toBeVisible()
})

test('diagnosis validates process and sends answer plus confusion', async ({ page }) => {
  let calls = 0
  let payload: Record<string, unknown> = {}
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    calls++
    payload = route.request().postDataJSON()
    await route.fulfill({
      json: { success: true, error: null, data: answer({ mode: 'DIAGNOSE' }) },
    })
  })
  await openLearning(page)
  await page.getByText('错因诊断', { exact: true }).click()
  await page.getByRole('textbox', { name: '原题' }).fill('二分查找最坏比较次数')
  await page.getByRole('button', { name: '开始错因诊断' }).click()
  await expect(page.getByText(/至少填写 5 个字符/)).toBeVisible()
  expect(calls).toBe(0)

  await page.getByRole('textbox', { name: '完整作答过程（必填）' }).fill('我连续除以二直到一')
  await page.getByRole('textbox', { name: '我的最终答案（选填）' }).fill('3 次')
  await page.getByRole('textbox', { name: '最困惑的位置（选填）' }).fill('是否计算最后一次比较')
  await page.getByRole('button', { name: '开始错因诊断' }).click()
  expect(payload.finalAnswer).toBe('3 次')
  expect(payload.confusion).toBe('是否计算最后一次比较')
})

test('attachment parse state can be inspected and removed', async ({ page }) => {
  await page.route('**/agent-api/v1/learning/attachments', async (route) => {
    await route.fulfill({
      json: {
        success: true,
        error: null,
        data: {
          id: 'attachment-1',
          originalName: '课堂笔记.pdf',
          mediaType: 'application/pdf',
          parseStatus: 'READY',
          extractedPreview: '队列与层序遍历',
        },
      },
    })
  })
  await openLearning(page)
  await page.locator('.attachment-area input[type=file]').setInputFiles({
    name: '课堂笔记.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('test'),
  })

  await expect(page.getByText('已提取文字')).toBeVisible()
  await page.getByRole('button', { name: '移除 课堂笔记.pdf' }).click()
  await expect(page.getByText('已提取文字')).toHaveCount(0)
})

test('correction sends a bounded valid summary instead of the full evidence payload', async ({
  page,
}) => {
  const payloads: Array<Record<string, unknown>> = []
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    payloads.push(route.request().postDataJSON())
    await route.fulfill({
      json: {
        success: true,
        error: null,
        data: answer({ workedExample: '很长的例题'.repeat(5000) }),
      },
    })
  })
  await openLearning(page)
  await page.getByRole('textbox', { name: '知识点', exact: true }).fill('层序遍历')
  await page.getByRole('button', { name: '生成分层讲义' }).click()
  await page.getByPlaceholder('指出疑问、资料冲突，或要求换一种讲法').fill('请换一种讲法')
  await page.getByRole('button', { name: '核对并修正' }).click()

  const previous = String(payloads[1]?.previousAnswer)
  expect(previous.length).toBeLessThanOrEqual(12000)
  expect(() => JSON.parse(previous)).not.toThrow()
  expect(JSON.parse(previous)).not.toHaveProperty('workedExample')
  expect(JSON.parse(previous)).not.toHaveProperty('sources')
})
