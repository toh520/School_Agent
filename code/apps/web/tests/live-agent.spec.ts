import { expect, request as createRequest, test } from '@playwright/test'

const coreBase = 'http://127.0.0.1:8080/api/v1'
const agentBase = 'http://127.0.0.1:8000/agent-api/v1'

async function login(username: string): Promise<string> {
  const api = await createRequest.newContext()
  const response = await api.post(`${coreBase}/auth/login`, {
    data: { username, password: 'Student@123' },
  })
  expect(response.status()).toBe(200)
  const token = (await response.json()).data.accessToken as string
  await api.dispose()
  return token
}

function doneEvent(body: string): Record<string, any> {
  const frame = body.split('\n\n').find((item) => item.startsWith('event: done\n'))
  expect(frame).toBeTruthy()
  return JSON.parse(frame!.match(/^data:\s*(.+)$/m)![1])
}

test('M04 persists multi-turn SSE, isolates owners and records feedback', async () => {
  test.setTimeout(120_000)
  const student1 = await login('student1')
  const student2 = await login('student2')
  const owner = await createRequest.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${student1}` },
  })
  const outsider = await createRequest.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${student2}` },
  })

  const created = await owner.post(`${agentBase}/conversations`, {
    data: { title: '第四阶段验收会话' },
  })
  expect(created.status()).toBe(201)
  const conversationId = (await created.json()).data.id as string

  const first = await owner.post(`${agentBase}/conversations/${conversationId}/messages`, {
    data: { content: '帮我制定考试复习计划' },
  })
  expect(first.status()).toBe(200)
  const firstDone = doneEvent(await first.text())
  expect(firstDone.result.intent).toBe('EXAM')
  expect(firstDone.result.status).toBe('NEEDS_INPUT')
  expect(firstDone.result.missingFields).toEqual(['考试时间', '考试科目'])

  const second = await owner.post(`${agentBase}/conversations/${conversationId}/messages`, {
    data: { content: '9月20日考计算机' },
    timeout: 90_000,
  })
  expect(second.status()).toBe(200)
  const secondBody = await second.text()
  expect(secondBody).toContain('event: tool')
  const secondDone = doneEvent(secondBody)
  expect(['COMPLETED', 'DEGRADED']).toContain(secondDone.result.status)
  expect(secondDone.result.basis).toContain('受控工具校验结果')

  const detail = await owner.get(`${agentBase}/conversations/${conversationId}`)
  expect(detail.status()).toBe(200)
  expect((await detail.json()).data.messages).toHaveLength(4)

  const denied = await outsider.get(`${agentBase}/conversations/${conversationId}`)
  expect(denied.status()).toBe(404)

  const feedback = await owner.put(`${agentBase}/results/${secondDone.resultVersionId}/feedback`, {
    data: { category: 'HELPFUL' },
  })
  expect(feedback.status()).toBe(200)

  const unconfirmedMemory = await owner.post(`${agentBase}/memories`, {
    data: { dataScope: 'CHAT_HISTORY', contentSummary: '偏好简洁回答', confirmed: false },
  })
  expect(unconfirmedMemory.status()).toBe(403)

  expect(
    (
      await owner.put(`${coreBase}/users/me/authorizations/CHAT_HISTORY`, {
        data: { granted: true },
      })
    ).status(),
  ).toBe(200)
  const memory = await owner.post(`${agentBase}/memories`, {
    data: { dataScope: 'CHAT_HISTORY', contentSummary: '偏好简洁回答', confirmed: true },
  })
  expect(memory.status()).toBe(201)
  const memoryId = (await memory.json()).data.id as string
  expect((await owner.get(`${agentBase}/memories`)).status()).toBe(200)
  expect(
    (
      await owner.put(`${agentBase}/memories/${memoryId}`, {
        data: { contentSummary: '偏好简洁且分段的回答', confirmed: true },
      })
    ).status(),
  ).toBe(200)
  expect((await owner.delete(`${agentBase}/memories/${memoryId}`)).status()).toBe(204)
  expect(
    (
      await owner.put(`${coreBase}/users/me/authorizations/CHAT_HISTORY`, {
        data: { granted: false },
      })
    ).status(),
  ).toBe(200)

  const contracts = await owner.get(`${agentBase}/tools`)
  expect(contracts.status()).toBe(200)
  expect((await contracts.json()).data[0]).toMatchObject({
    name: 'context_snapshot',
    requiredRole: 'STUDENT',
    accessLevel: 'READ',
    idempotent: true,
  })

  expect((await owner.delete(`${agentBase}/conversations/${conversationId}`)).status()).toBe(204)
  expect((await owner.get(`${agentBase}/conversations/${conversationId}`)).status()).toBe(404)
  await owner.dispose()
  await outsider.dispose()
})
