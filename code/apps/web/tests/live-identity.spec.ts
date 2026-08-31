import { expect, request as createRequest, test } from '@playwright/test'

const apiBase = 'http://127.0.0.1:8080'
const apiPath = '/api/v1'
const student2Id = '10000000-0000-0000-0000-000000000002'

interface TokenData {
  accessToken: string
  refreshToken: string
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

test('AT-01 login, refresh rotation and logout revocation work end to end', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const token = await login('student1', 'Student@123')

  const me = await api.get(`${apiPath}/users/me`, {
    headers: { Authorization: `Bearer ${token.accessToken}` },
  })
  expect(me.status()).toBe(200)
  const meBody = await me.json()
  expect(meBody.data.authorizations.DIET.granted).toBe(false)

  const refreshed = await api.post(`${apiPath}/auth/refresh`, {
    data: { refreshToken: token.refreshToken },
  })
  expect(refreshed.status()).toBe(200)
  const refreshedToken = (await refreshed.json()).data as TokenData

  const reused = await api.post(`${apiPath}/auth/refresh`, {
    data: { refreshToken: token.refreshToken },
  })
  expect(reused.status()).toBe(401)

  const logout = await api.post(`${apiPath}/auth/logout`, {
    headers: { Authorization: `Bearer ${refreshedToken.accessToken}` },
  })
  expect(logout.status()).toBe(200)

  const afterLogout = await api.get(`${apiPath}/users/me`, {
    headers: { Authorization: `Bearer ${refreshedToken.accessToken}` },
  })
  expect(afterLogout.status()).toBe(401)
  await api.dispose()
})

test('AT-15 enforces owner isolation, revoke cleanup and admin audit boundary', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const failedLogin = await api.post(`${apiPath}/auth/login`, {
    data: { username: 'unknown-user', password: 'wrong-password' },
  })
  expect(failedLogin.status()).toBe(401)

  const student = await login('student1', 'Student@123')
  const studentHeaders = { Authorization: `Bearer ${student.accessToken}` }

  const crossUser = await api.get(`${apiPath}/users/${student2Id}/profile`, {
    headers: studentHeaders,
  })
  expect(crossUser.status()).toBe(403)

  const granted = await api.put(`${apiPath}/users/me/authorizations/DIET`, {
    headers: studentHeaders,
    data: { granted: true },
  })
  expect(granted.status()).toBe(200)

  const revoked = await api.put(`${apiPath}/users/me/authorizations/DIET`, {
    headers: studentHeaders,
    data: { granted: false },
  })
  expect(revoked.status()).toBe(200)
  expect((await revoked.json()).data.granted).toBe(false)

  const studentAdminSearch = await api.get(`${apiPath}/admin/audit-events`, {
    headers: studentHeaders,
  })
  expect(studentAdminSearch.status()).toBe(403)

  const ownAudit = await api.get(
    `${apiPath}/users/me/audit-events?eventType=AUTHORIZATION_REVOKED`,
    { headers: studentHeaders },
  )
  expect(ownAudit.status()).toBe(200)
  expect((await ownAudit.json()).data.items.length).toBeGreaterThan(0)

  const admin = await login('admin1', 'Admin@123')
  const adminSearch = await api.get(`${apiPath}/admin/audit-events?module=IAM`, {
    headers: { Authorization: `Bearer ${admin.accessToken}` },
  })
  expect(adminSearch.status()).toBe(200)

  const failedLoginAudit = await api.get(`${apiPath}/admin/audit-events?eventType=LOGIN_FAILED`, {
    headers: { Authorization: `Bearer ${admin.accessToken}` },
  })
  expect(failedLoginAudit.status()).toBe(200)
  expect((await failedLoginAudit.json()).data.items.length).toBeGreaterThan(0)

  const deniedAccessAudit = await api.get(
    `${apiPath}/admin/audit-events?userId=${student2Id}&eventType=RESOURCE_ACCESS`,
    { headers: { Authorization: `Bearer ${admin.accessToken}` } },
  )
  expect(deniedAccessAudit.status()).toBe(200)
  expect((await deniedAccessAudit.json()).data.items[0].outcome).toBe('DENIED')

  await api.post(`${apiPath}/auth/logout`, { headers: studentHeaders })
  await api.post(`${apiPath}/auth/logout`, {
    headers: { Authorization: `Bearer ${admin.accessToken}` },
  })
  await api.dispose()
})

test('student registration creates an immediately usable default-deny account', async () => {
  const api = await createRequest.newContext({ baseURL: apiBase })
  const unique = String(Date.now()).slice(-8)
  const studentNumber = `20${unique}`
  const phone = `139${unique}`
  const username = `s_${unique}`

  const registered = await api.post(`${apiPath}/auth/register`, {
    data: {
      studentNumber,
      phone,
      realName: '注册测试学生',
      username,
      password: 'Register@123',
      confirmPassword: 'Register@123',
    },
  })
  expect(registered.status()).toBe(200)
  const token = (await registered.json()).data as TokenData

  const me = await api.get(`${apiPath}/users/me`, {
    headers: { Authorization: `Bearer ${token.accessToken}` },
  })
  expect(me.status()).toBe(200)
  const body = await me.json()
  expect(body.data.profile.studentNumber).toBe(studentNumber)
  expect(body.data.profile.phone).toBe(phone)
  expect(body.data.authorizations.EXAMS.granted).toBe(false)
  expect(body.data.authorizations.DIET.granted).toBe(false)

  await api.post(`${apiPath}/auth/logout`, {
    headers: { Authorization: `Bearer ${token.accessToken}` },
  })
  await api.dispose()
})
