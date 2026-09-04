import type { ApiResponse } from '../types/api'
import type {
  AttachmentView,
  LearningAnswer,
  LearningMode,
  LearningOverview,
  PracticeAttempt,
  PracticeItem,
  ReviewPlan,
} from '../types/learning'
import { agentHttp } from './http'

function dataOrThrow<T>(response: { data: ApiResponse<T> }, message: string): T {
  if (response.data.data === null) throw new Error(message)
  return response.data.data
}

export async function askLearningAssistant(input: {
  mode: LearningMode
  course: string
  prompt: string
  workProcess?: string
  previousAnswer?: string
  correction?: string
  attachmentIds?: string[]
  history?: Array<{ role: 'user' | 'assistant'; content: string }>
}): Promise<LearningAnswer> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<LearningAnswer>>('/learning/answers', input, { timeout: 0 }),
    '学习助手暂时无法回答',
  )
}

export async function uploadLearningAttachment(file: File): Promise<AttachmentView> {
  const body = new FormData()
  body.append('file', file)
  return dataOrThrow(
    await agentHttp.post<ApiResponse<AttachmentView>>('/learning/attachments', body, {
      timeout: 0,
    }),
    '附件解析失败',
  )
}

export async function generatePractices(input: {
  course: string
  knowledgePoint: string
  questionTypes: string[]
  difficulty: string
  count: number
}): Promise<PracticeItem[]> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<PracticeItem[]>>('/learning/practices', input, { timeout: 0 }),
    '练习生成失败',
  )
}

export async function evaluatePractice(input: {
  practiceId: string
  workProcess: string
  finalAnswer: string
}): Promise<PracticeAttempt> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<PracticeAttempt>>('/learning/practice-attempts', input, {
      timeout: 0,
    }),
    '作答评估失败',
  )
}

export async function generateReviewPlan(input: Record<string, unknown>): Promise<ReviewPlan> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<ReviewPlan>>('/learning/review-plans', input, { timeout: 0 }),
    '复习计划生成失败',
  )
}

export async function fetchLearningOverview(): Promise<LearningOverview> {
  return dataOrThrow(
    await agentHttp.get<ApiResponse<LearningOverview>>('/learning/overview'),
    '学习记录加载失败',
  )
}

export async function fetchReviewPlans(): Promise<Array<Record<string, unknown>>> {
  return dataOrThrow(
    await agentHttp.get<ApiResponse<Array<Record<string, unknown>>>>('/learning/review-plans'),
    '复习计划加载失败',
  )
}

export async function deleteReviewPlan(planId: string): Promise<void> {
  await agentHttp.delete(`/learning/review-plans/${planId}`)
}
