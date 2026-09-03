import axios from 'axios'

export const publicHttp = axios.create({ baseURL: '/api/v1', timeout: 8_000 })
export const authenticatedHttp = axios.create({ baseURL: '/api/v1', timeout: 8_000 })
export const agentHttp = axios.create({ baseURL: '/agent-api/v1', timeout: 8_000 })

let accessToken = ''

export function setAccessToken(token: string): void {
  accessToken = token
}

export function getAccessToken(): string {
  return accessToken
}

authenticatedHttp.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

agentHttp.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})
