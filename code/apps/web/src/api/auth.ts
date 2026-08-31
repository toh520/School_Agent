import type { ApiResponse } from '../types/api'
import type { RegisterForm, TokenResponse } from '../types/identity'
import { authenticatedHttp, publicHttp, setAccessToken } from './http'

const REFRESH_TOKEN_KEY = 'school-agent-refresh-token'

function acceptTokens(tokens: TokenResponse): TokenResponse {
  setAccessToken(tokens.accessToken)
  sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
  return tokens
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await publicHttp.post<ApiResponse<TokenResponse>>('/auth/login', {
    username,
    password,
  })
  if (!response.data.data) throw new Error('登录响应缺少数据')
  return acceptTokens(response.data.data)
}

export async function registerStudent(form: RegisterForm): Promise<TokenResponse> {
  const response = await publicHttp.post<ApiResponse<TokenResponse>>('/auth/register', form)
  if (!response.data.data) throw new Error('注册响应缺少数据')
  return acceptTokens(response.data.data)
}

export async function restoreSession(): Promise<TokenResponse | null> {
  const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) return null
  try {
    const response = await publicHttp.post<ApiResponse<TokenResponse>>('/auth/refresh', {
      refreshToken,
    })
    if (!response.data.data) return null
    return acceptTokens(response.data.data)
  } catch {
    clearSession()
    return null
  }
}

export async function logout(): Promise<void> {
  try {
    await authenticatedHttp.post('/auth/logout')
  } finally {
    clearSession()
  }
}

export function clearSession(): void {
  setAccessToken('')
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}
