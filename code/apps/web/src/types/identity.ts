export type UserRole = 'STUDENT' | 'INFO_ADMIN'
export type DataScope = 'EXAMS' | 'MASTERY' | 'DIET' | 'CHAT_HISTORY'

export interface UserSummary {
  id: string
  username: string
  role: UserRole
  nickname: string
}
export interface TokenResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  user: UserSummary
}
export interface RegisterForm {
  studentNumber: string
  phone: string
  realName: string
  username: string
  password: string
  confirmPassword: string
}
export interface Profile {
  id: string
  username: string
  studentNumber: string | null
  realName: string | null
  phone: string | null
  role: UserRole
  nickname: string
  avatarUrl: string | null
  contact: string | null
  updatedAt: string
}
export interface Preference {
  tastes: string[]
  budget: number | null
  avoidances: string[]
  allergens: string[]
  dietaryGoal: string | null
  updatedAt: string
}
export interface AuthorizationState {
  scope: DataScope
  granted: boolean
  changedAt: string
}
export interface MeData {
  profile: Profile
  preference: Preference
  authorizations: Record<DataScope, AuthorizationState>
}
export interface AuditEvent {
  id: number
  eventType: string
  module: string
  outcome: string
  occurredAt: string
}
export interface PageData<T> {
  items: T[]
  page: number
  size: number
  total: number
  totalPages: number
}
