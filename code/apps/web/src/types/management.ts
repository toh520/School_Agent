export type ResourceType =
  | 'CANTEEN'
  | 'STALL'
  | 'INGREDIENT'
  | 'DISH'
  | 'BOOK'
  | 'HOLDING'
  | 'KNOWLEDGE'
  | 'SYSTEM_CONFIG'

export type FieldKind =
  | 'TEXT'
  | 'LONG_TEXT'
  | 'IMAGE'
  | 'INTEGER'
  | 'DECIMAL'
  | 'URL'
  | 'LIST'
  | 'SELECT'

export interface FieldDefinition {
  key: string
  label: string
  kind: FieldKind
  required: boolean
  recommended: boolean
  options: string[]
  help: string
}

export interface ResourceSchema {
  type: ResourceType
  label: string
  fields: FieldDefinition[]
  csvHeader: string
}

export interface ManagedResource {
  id: string
  type: ResourceType
  values: Record<string, unknown>
  status: 'ACTIVE' | 'INACTIVE'
  completeness: number
  createdBy: string | null
  updatedBy: string | null
  createdAt: string
  updatedAt: string
}

export interface FieldError {
  row: number
  field: string
  message: string
}

export interface ImportPreview {
  type: ResourceType
  totalRows: number
  validRows: number
  errors: FieldError[]
  preview: ManagedResource[]
  committed: boolean
}

export interface AccountSummary {
  id: string
  username: string
  role: 'STUDENT' | 'INFO_ADMIN'
  status: 'ACTIVE' | 'DISABLED'
  nickname: string
  createdAt: string
  updatedAt: string
}

export interface OperationLog {
  id: number
  actorUserId: string | null
  actorUsername: string | null
  action: string
  resourceType: string
  resourceId: string | null
  resourceCode: string | null
  summary: string
  requestId: string | null
  occurredAt: string
}

export interface PageData<T> {
  items: T[]
  page: number
  size: number
  total: number
  totalPages: number
}
