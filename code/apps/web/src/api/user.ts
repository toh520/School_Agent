import type { ApiResponse } from '../types/api'
import type {
  AuditEvent,
  AuthorizationState,
  DataScope,
  MeData,
  PageData,
  Preference,
  Profile,
} from '../types/identity'
import { authenticatedHttp } from './http'

function dataOrThrow<T>(response: ApiResponse<T>): T {
  if (response.data === null) throw new Error(response.error?.message ?? '响应缺少数据')
  return response.data
}

export async function fetchMe(): Promise<MeData> {
  return dataOrThrow((await authenticatedHttp.get<ApiResponse<MeData>>('/users/me')).data)
}

export async function saveProfile(input: {
  nickname: string
  avatarUrl: string
  contact: string
}): Promise<Profile> {
  return dataOrThrow(
    (await authenticatedHttp.patch<ApiResponse<Profile>>('/users/me/profile', input)).data,
  )
}

export async function savePreference(input: {
  tastes: string[]
  budget: number | null
  avoidances: string[]
  allergens: string[]
  dietaryGoal: string
}): Promise<Preference> {
  return dataOrThrow(
    (await authenticatedHttp.put<ApiResponse<Preference>>('/users/me/preferences', input)).data,
  )
}

export async function setAuthorization(
  scope: DataScope,
  granted: boolean,
): Promise<AuthorizationState> {
  return dataOrThrow(
    (
      await authenticatedHttp.put<ApiResponse<AuthorizationState>>(
        `/users/me/authorizations/${scope}`,
        { granted },
      )
    ).data,
  )
}

export async function cleanupData(scopes: DataScope[]): Promise<void> {
  await authenticatedHttp.post('/users/me/data-cleanup', { scopes })
}

export async function fetchAuditEvents(): Promise<PageData<AuditEvent>> {
  return dataOrThrow(
    (
      await authenticatedHttp.get<ApiResponse<PageData<AuditEvent>>>(
        '/users/me/audit-events?size=20',
      )
    ).data,
  )
}
