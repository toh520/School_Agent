import type { ApiResponse } from '../types/api'
import type {
  AccountSummary,
  ImportPreview,
  ManagedResource,
  OperationLog,
  PageData,
  ResourceSchema,
  ResourceType,
} from '../types/management'
import { authenticatedHttp } from './http'

const BASE = '/admin/management'

function dataOrThrow<T>(response: { data: ApiResponse<T> }, message: string): T {
  if (response.data.data === null) throw new Error(message)
  return response.data.data
}

export async function fetchSchemas(): Promise<ResourceSchema[]> {
  const response = await authenticatedHttp.get<ApiResponse<ResourceSchema[]>>(`${BASE}/schemas`)
  return dataOrThrow(response, '资料类型响应缺少数据')
}

export async function fetchResources(
  type: ResourceType,
  query = '',
  page = 0,
  status: ManagedResource['status'] = 'ACTIVE',
): Promise<PageData<ManagedResource>> {
  const response = await authenticatedHttp.get<ApiResponse<PageData<ManagedResource>>>(
    `${BASE}/resources/${type}`,
    { params: { query, status, page, size: 20 } },
  )
  return dataOrThrow(response, '资料列表响应缺少数据')
}

export async function createResource(
  type: ResourceType,
  values: Record<string, unknown>,
): Promise<ManagedResource> {
  const response = await authenticatedHttp.post<ApiResponse<ManagedResource>>(
    `${BASE}/resources/${type}`,
    { values },
  )
  return dataOrThrow(response, '新增资料响应缺少数据')
}

export async function updateResource(
  type: ResourceType,
  id: string,
  values: Record<string, unknown>,
): Promise<ManagedResource> {
  const response = await authenticatedHttp.put<ApiResponse<ManagedResource>>(
    `${BASE}/resources/${type}/${id}`,
    { values },
  )
  return dataOrThrow(response, '更新资料响应缺少数据')
}

export async function deactivateResource(type: ResourceType, id: string): Promise<void> {
  await authenticatedHttp.delete(`${BASE}/resources/${type}/${id}`)
}

export async function validateCsv(type: ResourceType, csvContent: string): Promise<ImportPreview> {
  const response = await authenticatedHttp.post<ApiResponse<ImportPreview>>(
    `${BASE}/imports/validate`,
    { type, csvContent },
  )
  return dataOrThrow(response, '导入校验响应缺少数据')
}

export async function commitCsv(type: ResourceType, csvContent: string): Promise<ImportPreview> {
  const response = await authenticatedHttp.post<ApiResponse<ImportPreview>>(
    `${BASE}/imports/commit`,
    { type, csvContent },
  )
  return dataOrThrow(response, '导入响应缺少数据')
}

export async function fetchAccounts(query = '', page = 0): Promise<PageData<AccountSummary>> {
  const response = await authenticatedHttp.get<ApiResponse<PageData<AccountSummary>>>(
    `${BASE}/accounts`,
    { params: { query, page, size: 20 } },
  )
  return dataOrThrow(response, '账号列表响应缺少数据')
}

export async function setAccountStatus(
  userId: string,
  status: AccountSummary['status'],
): Promise<void> {
  await authenticatedHttp.patch(`${BASE}/accounts/${userId}/status`, { status })
}

export async function fetchOperationLogs(page = 0): Promise<PageData<OperationLog>> {
  const response = await authenticatedHttp.get<ApiResponse<PageData<OperationLog>>>(
    `${BASE}/operation-logs`,
    { params: { page, size: 20 } },
  )
  return dataOrThrow(response, '操作记录响应缺少数据')
}
