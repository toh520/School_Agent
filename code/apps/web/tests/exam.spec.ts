import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const userId = '10000000-0000-0000-0000-000000000001'
const examId = '40000000-0000-0000-0000-000000000001'

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

async function login(page: Page) {
  await page.goto('/')
  await page.getByLabel('账号').fill('student1')
  await page.getByLabel('密码').fill('Student@123')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('link', { name: '考试助手', exact: true }).click()
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
  await page.route('**/api/v1/exams/next', (route) =>
    route.fulfill({ json: { success: true, data: null, error: null } }),
  )
  await page.route('**/api/v1/health/system', (route) =>
    route.fulfill({ json: { success: true, data: { status: 'UP' }, error: null } }),
  )
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: {
          accessToken: 'access',
          refreshToken: 'refresh',
          tokenType: 'Bearer',
          expiresIn: 900,
          user: { id: userId, username: 'student1', role: 'STUDENT', nickname: '学生用户一' },
        },
        error: null,
      },
    }),
  )
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({ json: { success: true, data: me, error: null } }),
  )
})

const testAnswer = {
  mode: 'EXPLAIN',
  course: '数据结构',
  answer: '测试回答',
  steps: ['步骤一', '步骤二'],
  conclusion: '测试结论',
  diagnosis: [],
  correctedPoints: [],
  verification: '受控测试',
  validationStatus: 'PARTIAL',
  sources: [],
  limitations: ['资料不足'],
  prerequisiteKnowledge: [],
  keyConcepts: [],
  keyClaims: [],
  workedExample: '',
  commonMistakes: [],
  memoryTip: '',
  selfTestQuestion: '',
  selfTestAnswer: '',
  evidenceConflicts: [],
}

async function openLearning(page: Page) {
  await page.route('**/api/v1/exams', (route) =>
    route.fulfill({ json: { success: true, data: [], error: null } }),
  )
  await login(page)
  await page.getByRole('button', { name: 'AI 学习工作台', exact: true }).click()
}

test('saved attempt details remain readable after reload', async ({ page }) => {
  await page.route('**/agent-api/v1/learning/overview', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: {
          activities: [],
          mistakes: [
            {
              id: 'mistake-1',
              course: '数据结构',
              knowledge_point: '树的遍历',
              score: 80,
              question_type: '计算题',
              prompt: '历史题目',
              work_process: '先访问B再访问A',
              final_answer: 'BAC',
              standard_answer: 'ABC',
              step_analysis: '先根再左再右',
              cause_type: 'REASONING',
              diagnosis: { items: ['第一步顺序错误'] },
              corrected_conclusion: '前序必须先访问根节点',
              review_suggestion: '复习前序定义',
              source_label: 'AI 生成',
              validation_status: 'PARTIAL',
              created_at: '2026-09-04T00:00:00Z',
            },
          ],
          practices: [],
          attempts: [
            {
              id: 'attempt-1',
              course: '数据结构',
              score: 80,
              correct: false,
              prompt: '历史题目',
              work_process: '先访问B再访问A',
              final_answer: 'BAC',
              standard_answer: 'ABC',
              step_analysis: '先根再左再右',
              diagnosis: { items: ['第一步顺序错误'], reviewSuggestion: '复习前序定义' },
              source_label: 'AI生成',
              created_at: '2026-09-04T00:00:00Z',
            },
          ],
        },
      },
    }),
  )
  await openLearning(page)
  for (let i = 0; i < 2; i++) {
    await page.getByRole('button', { name: '错题本', exact: true }).click()
    await expect(page.getByText('先访问B再访问A')).toBeVisible()
    await expect(page.getByText('第一步顺序错误')).toBeVisible()
    if (i === 0) {
      await page.reload()
      await page.getByRole('button', { name: 'AI 学习工作台', exact: true }).click()
    }
  }
})

test('long conversation stays bounded and preserves initial problem', async ({ page }) => {
  const requests: Array<{ history: Array<{ content: string }> }> = []
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    requests.push(route.request().postDataJSON())
    await route.fulfill({ json: { success: true, data: testAnswer, error: null } })
  })
  await openLearning(page)
  for (let index = 0; index < 9; index++) {
    await page.getByPlaceholder(/输入知识点/).fill(`第${index}次问题`)
    await page.getByRole('button', { name: '生成分层讲义' }).click()
    await expect.poll(() => requests.length).toBe(index + 1)
    await expect(page.getByRole('button', { name: '生成分层讲义' })).toBeEnabled()
  }
  expect(requests[8]!.history).toHaveLength(12)
  expect(requests[8]!.history[0]!.content).toContain('第0次问题')
  expect(requests[8]!.history[10]!.content).toContain('第7次问题')
})

test('model failure does not add failed turns and records remain accessible', async ({ page }) => {
  let calls = 0
  let lastHistory: unknown[] = []
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    calls++
    lastHistory = route.request().postDataJSON().history
    await route.fulfill(
      calls === 2
        ? { status: 503, json: { success: false, error: { message: 'offline' } } }
        : { json: { success: true, data: testAnswer, error: null } },
    )
  })
  await page.route('**/agent-api/v1/learning/overview', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: { activities: [], mistakes: [], practices: [] },
        error: null,
      },
    }),
  )
  await openLearning(page)
  await page.getByPlaceholder(/输入知识点/).fill('第一次问题')
  for (let index = 0; index < 3; index++) {
    await page.getByRole('button', { name: '生成分层讲义' }).click()
    await expect.poll(() => calls).toBe(index + 1)
    await expect(page.getByRole('button', { name: '生成分层讲义' })).toBeEnabled()
  }
  expect(lastHistory).toHaveLength(2)
  await expect(page.getByText('测试结论')).toBeVisible()
  const loaded = page.waitForResponse('**/agent-api/v1/learning/overview')
  await page.getByRole('button', { name: '错题本', exact: true }).click()
  expect((await loaded).status()).toBe(200)
})

test('switching course away and back discards in-flight answer', async ({ page }) => {
  let release!: () => void
  const paused = new Promise<void>((resolve) => {
    release = resolve
  })
  let received = false
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    received = true
    await paused
    await route.fulfill({ json: { success: true, data: testAnswer, error: null } })
  })
  await openLearning(page)
  await page.getByPlaceholder(/输入知识点/).fill('旧话题问题')
  await page.getByRole('button', { name: '生成分层讲义' }).click()
  await expect.poll(() => received).toBe(true)
  for (const course of ['计算机网络', '数据结构']) {
    await page
      .locator('.question-sheet .compact-fields .field-block')
      .first()
      .locator('.el-select__wrapper')
      .click()
    await page.getByRole('option', { name: course, exact: true }).click()
  }
  release()
  await expect(page.getByRole('button', { name: '生成分层讲义' })).toBeEnabled()
  await expect(page.getByText('测试结论')).toHaveCount(0)
})

test('student can only view administrator-published exams', async ({ page }) => {
  await page.route('**/api/v1/exams', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: [
          {
            id: examId,
            subject: '数据结构',
            examDate: '2026-12-20',
            startTime: '09:00:00',
            endTime: '11:00:00',
            location: '教学楼 A201',
            createdAt: '2026-09-03T00:00:00Z',
            updatedAt: '2026-09-03T00:00:00Z',
          },
        ],
        error: null,
      },
    }),
  )
  await login(page)
  await expect(page.getByText('数据结构').first()).toBeVisible()
  await expect(page.getByText('教学楼 A201').first()).toBeVisible()
  await expect(page.getByRole('button', { name: '添加考试' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '编辑' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '删除' })).toHaveCount(0)
})

test('an exam already in progress does not say it starts later', async ({ page }) => {
  const today = new Date()
  const examDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  await page.route('**/api/v1/exams', (route) =>
    route.fulfill({
      json: {
        success: true,
        data: [
          {
            id: examId,
            subject: '正在考试科目',
            examDate,
            startTime: '00:00:00',
            endTime: '23:59:59',
            location: '教学楼 A201',
            createdAt: `${examDate}T00:00:00Z`,
            updatedAt: `${examDate}T00:00:00Z`,
          },
        ],
        error: null,
      },
    }),
  )

  await login(page)
  const focus = page.locator('.exam-focus-date')
  await expect(focus).toContainText('正在进行')
  await expect(focus).not.toContainText('后开始')
})

test('student asks a grounded question and can submit a correction', async ({ page }) => {
  await page.route('**/api/v1/exams', (route) =>
    route.fulfill({ json: { success: true, data: [], error: null } }),
  )
  let requestedMode = ''
  let requestHistory: Array<{ role: string; content: string }> = []
  await page.route('**/agent-api/v1/learning/answers', async (route) => {
    requestedMode = route.request().postDataJSON().mode
    requestHistory = route.request().postDataJSON().history
    await route.fulfill({
      json: {
        success: true,
        data: {
          mode: requestedMode,
          course: '数据结构',
          answer: '二叉树高度可以递归计算。',
          steps: ['计算左子树', '计算右子树', '取较大值加一'],
          conclusion: '高度等于两棵子树较大高度加一。',
          diagnosis: [],
          correctedPoints: requestedMode === 'CORRECT' ? ['已补充空树边界'] : [],
          verification: '与课程资料定义一致',
          validationStatus: 'MATERIAL_SUPPORTED',
          sources: [
            {
              materialId: 'm1',
              fileName: '数据结构.pdf',
              locator: '第 2 页',
              snippet: '树的高度等于左右子树最大高度加一。',
            },
          ],
          limitations: [],
          prerequisiteKnowledge: ['递归'],
          keyConcepts: ['空树边界', '子树高度'],
          keyClaims: [
            {
              text: '高度等于左右子树最大高度加一',
              origin: 'COURSE_MATERIAL',
              sources: [
                {
                  materialId: 'm1',
                  fileName: '数据结构.pdf',
                  locator: '第 2 页',
                  snippet: '树的高度等于左右子树最大高度加一。',
                },
              ],
            },
          ],
          workedExample: '空树高度按课程约定处理。',
          commonMistakes: ['遗漏空树边界'],
          memoryTip: '先递归子树，再取最大值。',
          selfTestQuestion: '只有根节点的树高度是多少？',
          selfTestAnswer: '按边计数为 0，按层计数为 1。',
          evidenceConflicts: [],
        },
        error: null,
      },
    })
  })

  await login(page)
  await page.getByRole('button', { name: 'AI 学习工作台', exact: true }).click()
  await page.getByPlaceholder(/输入知识点/).fill('如何计算二叉树高度？')
  await page.getByRole('button', { name: '生成分层讲义' }).click()
  await expect(page.getByText('高度等于两棵子树较大高度加一。')).toBeVisible()
  await expect(page.getByText('课程资料依据')).toBeVisible()
  await page.getByText('数据结构.pdf · 第 2 页').click()
  await expect(page.getByText('树的高度等于左右子树最大高度加一。')).toBeVisible()
  await page.getByPlaceholder('指出疑问、资料冲突，或要求换一种讲法').fill('请补充空树的情况')
  await page.getByRole('button', { name: '核对并修正' }).click()
  await expect(page.getByText('已补充空树边界')).toBeVisible()
  expect(requestedMode).toBe('CORRECT')
  expect(requestHistory[0]?.content).toContain('如何计算二叉树高度')
  await page.getByPlaceholder(/输入知识点/).fill('刚才空树边界再解释一下')
  await page.getByRole('button', { name: '生成分层讲义' }).click()
  await expect.poll(() => requestHistory.length).toBe(4)
  expect(requestHistory[2]?.content).toContain('请补充空树的情况')
  await expect(page.getByRole('button', { name: '生成分层讲义' })).toBeEnabled()
  await page.getByRole('button', { name: '新话题', exact: true }).click()
  await page.getByPlaceholder(/输入知识点/).fill('新题：图的遍历')
  await page.getByRole('button', { name: '生成分层讲义' }).click()
  await expect.poll(() => requestHistory.length).toBe(0)
})

test('student generates a traceable review plan with fixed stage quotas', async ({ page }) => {
  await page.route('**/api/v1/exams', (route) =>
    route.fulfill({
      json: {
        success: true,
        error: null,
        data: [
          {
            id: examId,
            subject: '数据结构',
            examDate: '2026-12-20',
            startTime: '09:00:00',
            endTime: '11:00:00',
            location: '教学楼 A201',
            createdAt: '2026-09-03T00:00:00Z',
            updatedAt: '2026-09-05T00:00:00Z',
          },
        ],
      },
    }),
  )
  let savedPlan: Record<string, unknown> | null = null
  await page.route('**/agent-api/v1/learning/review-plans', async (route) => {
    if (route.request().method() === 'GET') {
      return route.fulfill({
        json: { success: true, data: savedPlan ? [savedPlan] : [], error: null },
      })
    }
    const input = route.request().postDataJSON()
    savedPlan = {
      id: 'plan-1',
      planGroupId: 'group-1',
      versionNumber: 1,
      isCurrent: true,
      title: '数据结构复习计划',
      status: 'ACTIVE',
      target: input.target,
      constraints: input.constraints,
      inputSnapshot: input,
      priorityExplanation: '按考试迫近程度与错题证据分配时间。',
      assumptions: ['每日按设定时长学习'],
      limitations: ['不替代学校通知'],
      totalMinutes: 600,
      modelName: 'test-model',
      dataAsOf: '2026-09-06T08:00:00Z',
      createdAt: '2026-09-06T08:00:00Z',
      stale: false,
      exams: [],
      stages: [
        {
          id: 'stage-1',
          stageIndex: 0,
          name: '数据结构 · 基础回顾',
          phase: 'FOUNDATION',
          startDate: '2026-09-06',
          endDate: '2026-12-10',
          subject: '数据结构',
          knowledgePoints: ['树的遍历'],
          objective: '建立知识框架',
          suggestedMinutes: 330,
          method: '精读讲义并整理错题',
          rationale: '树的遍历有未掌握错题证据',
        },
      ],
    }
    return route.fulfill({ json: { success: true, data: savedPlan, error: null } })
  })

  await login(page)
  await page.getByRole('button', { name: 'AI 学习工作台', exact: true }).click()
  await page.getByRole('button', { name: '复习计划', exact: true }).click()
  await page.getByText('数据结构').last().click()
  await page.getByPlaceholder('例如：掌握核心题型，稳定达到 80 分').fill('稳定达到 80 分')
  await page.getByRole('button', { name: '生成并保存计划' }).click()

  await expect(page.getByText('600 分钟')).toBeVisible()
  await expect(page.getByText('建立知识框架')).toBeVisible()
  await expect(page.getByText('树的遍历有未掌握错题证据')).toBeVisible()
})
