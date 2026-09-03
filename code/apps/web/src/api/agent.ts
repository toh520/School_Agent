import type { ApiResponse } from '../types/api'
import type {
  AgentStreamCallbacks,
  AgentMemory,
  ConversationDetail,
  ConversationSummary,
  FeedbackCategory,
} from '../types/agent'
import { agentHttp, getAccessToken } from './http'

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await agentHttp.get<ApiResponse<ConversationSummary[]>>('/conversations')
  return response.data.data ?? []
}

export async function createConversation(title = '新会话'): Promise<ConversationSummary> {
  const response = await agentHttp.post<ApiResponse<ConversationSummary>>('/conversations', {
    title,
  })
  if (!response.data.data) throw new Error('创建会话失败')
  return response.data.data
}

export async function fetchConversation(id: string): Promise<ConversationDetail> {
  const response = await agentHttp.get<ApiResponse<ConversationDetail>>(`/conversations/${id}`)
  if (!response.data.data) throw new Error('读取会话失败')
  return response.data.data
}

export async function deleteConversation(id: string): Promise<void> {
  await agentHttp.delete(`/conversations/${id}`)
}

export async function saveFeedback(resultId: string, category: FeedbackCategory): Promise<void> {
  await agentHttp.put(`/results/${resultId}/feedback`, { category })
}

export async function fetchMemories(): Promise<AgentMemory[]> {
  const response = await agentHttp.get<ApiResponse<AgentMemory[]>>('/memories')
  return response.data.data ?? []
}

export async function saveMemory(
  dataScope: AgentMemory['dataScope'],
  contentSummary: string,
): Promise<void> {
  await agentHttp.post('/memories', { dataScope, contentSummary, confirmed: true })
}

export async function updateMemory(id: string, contentSummary: string): Promise<void> {
  await agentHttp.put(`/memories/${id}`, { contentSummary, confirmed: true })
}

export async function deleteMemory(id: string): Promise<void> {
  await agentHttp.delete(`/memories/${id}`)
}

export async function streamMessage(
  conversationId: string,
  content: string,
  callbacks: AgentStreamCallbacks,
): Promise<void> {
  await stream(`/conversations/${conversationId}/messages`, { content }, callbacks)
}

export async function regenerateTask(
  taskId: string,
  callbacks: AgentStreamCallbacks,
): Promise<void> {
  await stream(`/tasks/${taskId}/regenerate`, undefined, callbacks)
}

async function stream(
  path: string,
  body: Record<string, unknown> | undefined,
  callbacks: AgentStreamCallbacks,
): Promise<void> {
  const response = await fetch(`/agent-api/v1${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${getAccessToken()}`,
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok || !response.body) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.error?.message ?? '智能服务暂时无法响应')
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) dispatchFrame(frame, callbacks)
    if (done) break
  }
  if (buffer.trim()) dispatchFrame(buffer, callbacks)
}

function dispatchFrame(frame: string, callbacks: AgentStreamCallbacks): void {
  const event = frame.match(/^event:\s*(.+)$/m)?.[1]
  const raw = frame.match(/^data:\s*(.+)$/m)?.[1]
  if (!event || !raw) return
  const data = JSON.parse(raw)
  if (event === 'status') callbacks.onStatus(data)
  if (event === 'intent') callbacks.onIntent(data)
  if (event === 'tool') callbacks.onTool(data)
  if (event === 'content') callbacks.onContent(data)
  if (event === 'done') callbacks.onDone(data)
}
