import { expect, request as createRequest, test } from '@playwright/test'

const coreBase = 'http://127.0.0.1:8080/api/v1'

test('administrator publishes an exam that is immediately queryable', async () => {
  const api = await createRequest.newContext()
  const login = await api.post(`${coreBase}/auth/login`, {
    data: { username: 'admin1', password: 'Admin@123' },
  })
  expect(login.status()).toBe(200)
  const token = (await login.json()).data.accessToken as string
  const admin = await createRequest.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
  })
  let examId = ''
  let examUrl = ''
  try {
    const accounts = await admin.get(`${coreBase}/admin/management/accounts`, {
      params: { query: 'student1', page: 0, size: 20 },
    })
    expect(accounts.status()).toBe(200)
    const student = (await accounts.json()).data.items.find(
      (item: { username: string }) => item.username === 'student1',
    )
    expect(student).toBeTruthy()
    examUrl = `${coreBase}/admin/management/exams/users/${student.id}`

    const created = await admin.post(examUrl, {
      data: {
        subject: '考试接口回归测试',
        examDate: '2026-12-31',
        startTime: '09:00:00',
        endTime: '11:00:00',
        location: '测试地点',
      },
    })
    expect(created.status()).toBe(201)
    examId = (await created.json()).data.id as string

    const exams = await admin.get(examUrl)
    expect(exams.status()).toBe(200)
    expect((await exams.json()).data).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: examId, subject: '考试接口回归测试' }),
      ]),
    )
  } finally {
    if (examId) await admin.delete(`${examUrl}/${examId}`)
    await admin.dispose()
    await api.dispose()
  }
})
