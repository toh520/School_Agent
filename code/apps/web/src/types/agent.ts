export type AgentIntent = 'FOOD' | 'EXAM' | 'BOOK' | 'CAMPUS_QA' | 'UNKNOWN'
export type TaskStatus = 'RUNNING' | 'NEEDS_INPUT' | 'COMPLETED' | 'DEGRADED' | 'FAILED'
export type FeedbackCategory = 'HELPFUL' | 'UNHELPFUL' | 'INCORRECT' | 'OUTDATED'

export interface ConversationSummary {
  id: string
  title: string
  currentIntent: AgentIntent | null
  updatedAt: string
}

export interface AgentMessage {
  id: string
  role: 'USER' | 'ASSISTANT' | 'TOOL'
  content: string
  sequenceNumber: number
  resultVersionId: string | null
  taskId: string | null
  intent: AgentIntent | null
  fallbackUsed: boolean
  basis: string[]
  limitations: string[]
  createdAt: string
}

export interface ConversationDetail extends ConversationSummary {
  messages: AgentMessage[]
}

export interface WorkflowResult {
  intent: AgentIntent
  status: TaskStatus
  missingFields: string[]
  content: string
  structuredResult: Record<string, unknown>
  basis: string[]
  limitations: string[]
  modelName: string | null
  fallbackUsed: boolean
}

export interface PersistedTurn {
  taskId: string
  messageId: string
  resultVersionId: string
  result: WorkflowResult
}

export interface AgentMemory {
  id: string
  dataScope: 'EXAMS' | 'MASTERY' | 'DIET' | 'CHAT_HISTORY'
  contentSummary: string
  createdAt: string
}

export interface AgentStreamCallbacks {
  onStatus: (data: { phase: string; label: string; fields?: string[] }) => void
  onIntent: (data: { intent: AgentIntent }) => void
  onTool: (data: { name: string; status: string; durationMs: number }) => void
  onContent: (data: { delta: string }) => void
  onDone: (data: PersistedTurn) => void
}
