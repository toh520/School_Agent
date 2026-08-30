import axios from 'axios'

import type { ApiResponse, SystemHealth } from '../types/api'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 5_000,
})

export async function fetchSystemHealth(): Promise<ApiResponse<SystemHealth>> {
  const response = await http.get<ApiResponse<SystemHealth>>('/health/system')
  return response.data
}
