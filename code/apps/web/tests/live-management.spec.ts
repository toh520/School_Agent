import { expect, request as createRequest, test } from '@playwright/test'

const apiBase = 'http://127.0.0.1:8080'
const apiPath = '/api/v1'
const managementPath = `${apiPath}/admin/management`

interface TokenData {
  accessToken: string
}

async function login(username: string, password: string): Promise<TokenData> {
  const context = await createRequest.newContext({ baseURL: apiBase })
  const response = await context.post(`${apiPath}/auth/login`, {
    data: { username, password },
  })
  expect(response.status()).toBe(200)
  const body = await response.json()
  await context.dispose()
  return body.data as TokenData
}

test('AT-16 isolates management APIs and completes resource lifecycle', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const student = await login('student1', 'Student@123')
  const denied = await api.get(`${managementPath}/schemas`, {
    headers: { Authorization: `Bearer ${student.accessToken}` },
  })
  expect(denied.status()).toBe(403)

  const admin = await login('admin1', 'Admin@123')
  const headers = { Authorization: `Bearer ${admin.accessToken}` }
  const suffix = String(Date.now())
  const code = `AT16-${suffix}`

  const created = await api.post(`${managementPath}/resources/CANTEEN`, {
    headers,
    data: {
      values: {
        code,
        name: '验收食堂',
        location: '验收校区',
        openingHours: '07:00-20:00',
        source: '第三阶段自动验收',
      },
    },
  })
  expect(created.status()).toBe(200)
  const resource = (await created.json()).data
  expect(resource.completeness).toBe(100)

  const duplicate = await api.post(`${managementPath}/resources/CANTEEN`, {
    headers,
    data: { values: resource.values },
  })
  expect(duplicate.status()).toBe(409)

  const searched = await api.get(`${managementPath}/resources/CANTEEN`, {
    headers,
    params: { query: code },
  })
  expect(searched.status()).toBe(200)
  expect((await searched.json()).data.items).toHaveLength(1)

  const updated = await api.put(`${managementPath}/resources/CANTEEN/${resource.id}`, {
    headers,
    data: {
      values: {
        ...resource.values,
        name: '验收食堂（已更新）',
      },
    },
  })
  expect(updated.status()).toBe(200)
  expect((await updated.json()).data.values.name).toBe('验收食堂（已更新）')

  const deactivated = await api.delete(`${managementPath}/resources/CANTEEN/${resource.id}`, {
    headers,
  })
  expect(deactivated.status()).toBe(200)

  const inactive = await api.get(`${managementPath}/resources/CANTEEN`, {
    headers,
    params: { query: code, status: 'INACTIVE' },
  })
  expect(inactive.status()).toBe(200)
  expect((await inactive.json()).data.items[0].status).toBe('INACTIVE')

  const logs = await api.get(`${managementPath}/operation-logs`, { headers })
  expect(logs.status()).toBe(200)
  const matchingLogs = (await logs.json()).data.items.filter(
    (item: { resourceCode: string }) => item.resourceCode === code,
  )
  const matchingActions = matchingLogs.map((item: { action: string }) => item.action)
  expect(matchingActions).toEqual(expect.arrayContaining(['CREATE', 'UPDATE', 'DEACTIVATE']))
  expect(
    matchingLogs.every((item: { actorUsername: string }) => item.actorUsername === 'admin1'),
  ).toBe(true)
  expect(matchingLogs.every((item: { requestId: string }) => Boolean(item.requestId))).toBe(true)

  const pagedLogs = await api.get(`${managementPath}/operation-logs`, {
    headers,
    params: { page: 1, size: 1 },
  })
  expect(pagedLogs.status()).toBe(200)
  const pagedLogBody = (await pagedLogs.json()).data
  expect(pagedLogBody.page).toBe(1)
  expect(pagedLogBody.size).toBe(1)
  expect(pagedLogBody.items).toHaveLength(1)
  await api.dispose()
})

test('AT-18 prevalidates CSV and commits only valid batches', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const admin = await login('admin1', 'Admin@123')
  const headers = { Authorization: `Bearer ${admin.accessToken}` }
  const suffix = String(Date.now())
  const code = `AT18-${suffix}`
  const invalidCsv =
    'code,name,category,taste,nutritionKcal,nutritionProtein,allergens,source\n' +
    `${code},验收食材,谷物,清淡,-1,8,,第三阶段自动验收\n`

  const invalid = await api.post(`${managementPath}/imports/validate`, {
    headers,
    data: { type: 'INGREDIENT', csvContent: invalidCsv },
  })
  expect(invalid.status()).toBe(200)
  const invalidBody = (await invalid.json()).data
  expect(invalidBody.committed).toBe(false)
  expect(invalidBody.errors).toContainEqual(
    expect.objectContaining({ row: 2, field: 'nutritionKcal' }),
  )

  const validCsv = invalidCsv.replace(',-1,', ',350,')
  const preview = await api.post(`${managementPath}/imports/validate`, {
    headers,
    data: { type: 'INGREDIENT', csvContent: validCsv },
  })
  expect(preview.status()).toBe(200)
  expect((await preview.json()).data.errors).toHaveLength(0)

  const committed = await api.post(`${managementPath}/imports/commit`, {
    headers,
    data: { type: 'INGREDIENT', csvContent: validCsv },
  })
  expect(committed.status()).toBe(200)
  const committedBody = (await committed.json()).data
  expect(committedBody.committed).toBe(true)
  expect(committedBody.preview[0].values.code).toBe(code)

  const resourceId = committedBody.preview[0].id
  const deactivated = await api.delete(`${managementPath}/resources/INGREDIENT/${resourceId}`, {
    headers,
  })
  expect(deactivated.status()).toBe(200)
  await api.dispose()
})

test('campus announcements keep only searchable text fields', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const admin = await login('admin1', 'Admin@123')
  const headers = { Authorization: `Bearer ${admin.accessToken}` }

  const schemas = await api.get(`${managementPath}/schemas`, { headers })
  expect(schemas.status()).toBe(200)
  const schemaList = (await schemas.json()).data
  expect(schemaList).toHaveLength(8)
  const knowledgeSchema = schemaList.find((schema: { type: string }) => schema.type === 'KNOWLEDGE')
  expect(knowledgeSchema.fields.map((field: { key: string }) => field.key)).toEqual([
    'code',
    'name',
    'category',
    'keywords',
    'body',
    'source',
  ])

  const suffix = String(Date.now())
  const code = `NOTICE-${suffix}`
  const keyword = `检索词${suffix}`
  const created = await api.post(`${managementPath}/resources/KNOWLEDGE`, {
    headers,
    data: {
      values: {
        code,
        name: '校园公告检索验收',
        category: '校园服务',
        keywords: ['开放时间', keyword],
        body: '公告正文用于后续 RAG 检索和回答。',
        source: '学校公开公告',
      },
    },
  })
  expect(created.status()).toBe(200)
  const resource = (await created.json()).data
  expect(resource.values.keywords).toEqual(['开放时间', keyword])

  const searched = await api.get(`${managementPath}/resources/KNOWLEDGE`, {
    headers,
    params: { query: keyword },
  })
  expect(searched.status()).toBe(200)
  expect((await searched.json()).data.items[0].id).toBe(resource.id)

  const deactivated = await api.delete(`${managementPath}/resources/KNOWLEDGE/${resource.id}`, {
    headers,
  })
  expect(deactivated.status()).toBe(200)
  await api.dispose()
})
