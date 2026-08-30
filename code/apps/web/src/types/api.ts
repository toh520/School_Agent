export interface ApiError {
  code: string
  message: string
}

export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: ApiError | null
  requestId: string
  timestamp: string
}

export interface DependencyHealth {
  status: string
  version?: string
}

export interface SystemHealth {
  status: string
  coreService: DependencyHealth
  agentService: DependencyHealth
  database: DependencyHealth
}
