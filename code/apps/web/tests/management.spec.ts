import { expect, test } from '@playwright/test'

const schema = {
  type: 'SYSTEM_CONFIG',
  label: '公共配置',
  csvHeader: 'code,name,configValue,description,source',
  fields: [
    {
      key: 'code',
      label: '配置键',
      kind: 'TEXT',
      required: true,
      recommended: false,
      options: [],
      help: '稳定唯一编码',
    },
    {
      key: 'name',
      label: '配置名称',
      kind: 'TEXT',
      required: true,
      recommended: false,
      options: [],
      help: '正式名称',
    },
    {
      key: 'configValue',
      label: '配置值',
      kind: 'LONG_TEXT',
      required: true,
      recommended: false,
      options: [],
      help: '非敏感公共配置',
    },
    {
      key: 'description',
      label: '说明',
      kind: 'LONG_TEXT',
      required: false,
      recommended: false,
      options: [],
      help: '服务说明',
    },
    {
      key: 'source',
      label: '信息来源',
      kind: 'TEXT',
      required: true,
      recommended: false,
      options: [],
      help: '责任部门',
    },
  ],
}

const adminMe = {
  profile: {
    id: '20000000-0000-0000-0000-000000000001',
    username: 'admin1',
    studentNumber: null,
    realName: null,
    phone: null,
    role: 'INFO_ADMIN',
    nickname: '信息资料管理员',
    avatarUrl: null,
    contact: null,
    updatedAt: '2026-08-31T12:00:00Z',
  },
  preference: {
    tastes: [],
    budget: null,
    avoidances: [],
    allergens: [],
    dietaryGoal: null,
    updatedAt: '2026-08-31T12:00:00Z',
  },
  authorizations: {},
}

function envelope(data: unknown) {
  return {
    success: true,
    data,
    error: null,
    requestId: 'm03-test',
    timestamp: '2026-08-31T12:00:00Z',
  }
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/admin/management/resources/DISH*', (route) =>
    route.fulfill({ json: envelope({ items: [], page: 0, size: 20, total: 0, totalPages: 0 }) }),
  )
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      json: envelope({
        accessToken: 'admin-access',
        refreshToken: 'admin-refresh',
        tokenType: 'Bearer',
        expiresIn: 900,
        user: {
          id: adminMe.profile.id,
          username: 'admin1',
          role: 'INFO_ADMIN',
          nickname: '信息资料管理员',
        },
      }),
    }),
  )
  await page.route('**/api/v1/users/me', (route) => route.fulfill({ json: envelope(adminMe) }))
  await page.route('**/api/v1/admin/management/schemas', (route) =>
    route.fulfill({ json: envelope([schema]) }),
  )
})

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto('/')
  await page.getByLabel('账号').fill('admin1')
  await page.getByLabel('密码').fill('Admin@123')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  // Generic CRUD/import now lives under public configuration, not the removed canteen view.
  await page.getByRole('button', { name: '公共配置', exact: true }).click()
}

test('administrator sees the unified registry and creates a validated resource', async ({
  page,
}) => {
  let created = false
  await page.route('**/api/v1/admin/management/resources/SYSTEM_CONFIG*', async (route) => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON()
      expect(body.values).toMatchObject({
        code: 'DISPLAY-TITLE',
        name: '页面标题',
        configValue: '智慧校园',
        source: '后勤公示',
      })
      created = true
      await route.fulfill({
        json: envelope({
          id: '30000000-0000-0000-0000-000000000001',
          type: 'SYSTEM_CONFIG',
          values: body.values,
          status: 'ACTIVE',
          completeness: 80,
          createdBy: adminMe.profile.id,
          updatedBy: adminMe.profile.id,
          createdAt: '2026-08-31T12:00:00Z',
          updatedAt: '2026-08-31T12:00:00Z',
        }),
      })
      return
    }
    await route.fulfill({
      json: envelope({ items: [], page: 0, size: 20, total: 0, totalPages: 0 }),
    })
  })

  await loginAsAdmin(page)
  await expect(page.getByRole('heading', { name: '公共配置资料' })).toBeVisible()
  await page.getByRole('button', { name: '新增资料' }).click()
  await page.getByPlaceholder('稳定唯一编码').fill('DISPLAY-TITLE')
  await page.getByPlaceholder('正式名称').fill('页面标题')
  await page.getByPlaceholder('非敏感公共配置').fill('智慧校园')
  await page.getByPlaceholder('责任部门').fill('后勤公示')
  await page.getByRole('button', { name: '创建资料' }).click()

  await expect.poll(() => created).toBe(true)
  await expect(page.getByText('资料已创建')).toBeVisible()
})

test('CSV preview identifies the exact invalid row and blocks commit', async ({ page }) => {
  await page.route('**/api/v1/admin/management/resources/SYSTEM_CONFIG*', (route) =>
    route.fulfill({ json: envelope({ items: [], page: 0, size: 20, total: 0, totalPages: 0 }) }),
  )
  await page.route('**/api/v1/admin/management/imports/validate', (route) =>
    route.fulfill({
      json: envelope({
        type: 'SYSTEM_CONFIG',
        totalRows: 1,
        validRows: 0,
        errors: [{ row: 2, field: 'source', message: '信息来源为必填项' }],
        preview: [],
        committed: false,
      }),
    }),
  )

  await loginAsAdmin(page)
  await page.getByRole('button', { name: '批量导入' }).click()
  await page.getByLabel('选择CSV文件').setInputFiles({
    name: 'config.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('code,name,configValue,description,source\nDISPLAY-X,临时配置,测试,,'),
  })
  await page.getByRole('button', { name: '预校验' }).click()

  await expect(page.getByRole('cell', { name: '2', exact: true })).toBeVisible()
  await expect(page.getByText('信息来源为必填项')).toBeVisible()
  await expect(page.getByRole('button', { name: '确认入库' })).toBeDisabled()
})

test('resource ledger paginates and filters inactive records', async ({ page }) => {
  const requests: string[] = []
  await page.route('**/api/v1/admin/management/resources/SYSTEM_CONFIG*', (route) => {
    const url = new URL(route.request().url())
    requests.push(url.search)
    const status = url.searchParams.get('status') === 'INACTIVE' ? 'INACTIVE' : 'ACTIVE'
    const pageIndex = Number(url.searchParams.get('page') ?? 0)
    return route.fulfill({
      json: envelope({
        items: [
          {
            id: `${status}-${pageIndex}`,
            type: 'SYSTEM_CONFIG',
            values: { code: `CONFIG-${pageIndex}`, name: '分页资料', source: '后勤公示' },
            status,
            completeness: 75,
            createdBy: adminMe.profile.id,
            updatedBy: adminMe.profile.id,
            createdAt: '2026-08-31T12:00:00Z',
            updatedAt: '2026-08-31T12:00:00Z',
          },
        ],
        page: pageIndex,
        size: 20,
        total: 21,
        totalPages: 2,
      }),
    })
  })

  await loginAsAdmin(page)
  await expect(page.getByText('75%')).toBeVisible()
  await page.locator('.el-pager li').filter({ hasText: '2' }).click()
  await expect.poll(() => requests.some((value) => value.includes('page=1'))).toBe(true)

  await page.locator('.registry-filter .el-select__wrapper').click()
  await page.getByRole('option', { name: '已停用资料' }).click()
  await expect
    .poll(() =>
      requests.some((value) => value.includes('status=INACTIVE') && value.includes('page=0')),
    )
    .toBe(true)
  await expect(page.getByText('已停用', { exact: true })).toBeVisible()
})

test('operation ledger shows actor, action, resource and request id', async ({ page }) => {
  let requestedPage = -1
  await page.route('**/api/v1/admin/management/resources/SYSTEM_CONFIG*', (route) =>
    route.fulfill({ json: envelope({ items: [], page: 0, size: 20, total: 0, totalPages: 0 }) }),
  )
  await page.route('**/api/v1/admin/management/operation-logs*', (route) => {
    const url = new URL(route.request().url())
    requestedPage = Number(url.searchParams.get('page') ?? 0)
    return route.fulfill({
      json: envelope({
        items: [
          {
            id: requestedPage + 1,
            actorUserId: adminMe.profile.id,
            actorUsername: 'admin1',
            action: 'UPDATE',
            resourceType: 'CANTEEN',
            resourceId: '30000000-0000-0000-0000-000000000001',
            resourceCode: 'CANTEEN-NORTH',
            summary: '食堂已更新',
            requestId: 'request-page-test',
            occurredAt: '2026-08-31T12:00:00Z',
          },
        ],
        page: requestedPage,
        size: 20,
        total: 21,
        totalPages: 2,
      }),
    })
  })

  await loginAsAdmin(page)
  await page.getByRole('button', { name: '操作记录' }).click()
  await expect(page.getByText('admin1', { exact: true })).toBeVisible()
  await expect(page.getByText(adminMe.profile.id, { exact: true })).toBeVisible()
  await expect(page.getByText('编辑', { exact: true })).toBeVisible()
  await expect(page.getByText('CANTEEN-NORTH', { exact: true })).toBeVisible()
  await expect(page.getByText('request-page-test', { exact: true })).toBeVisible()

  await page.locator('.el-pager li').filter({ hasText: '2' }).click()
  await expect.poll(() => requestedPage).toBe(1)
})
