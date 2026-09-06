import type { ApiResponse } from '../types/api'
import type { ExamInput, ExamRecord } from '../types/exam'
import { authenticatedHttp } from './http'

function dataOrThrow<T>(response: { data: ApiResponse<T> }, message: string): T {
  if (response.data.data === null) throw new Error(message)
  return response.data.data
}

export async function fetchExams(): Promise<ExamRecord[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<ExamRecord[]>>('/exams'),
    '考试安排加载失败',
  )
}

export async function fetchNextExam(): Promise<ExamRecord | null> {
  const response = await authenticatedHttp.get<ApiResponse<ExamRecord>>('/exams/next')
  return response.data.data
}

export async function createAdminExam(userId: string, input: ExamInput): Promise<ExamRecord> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<ExamRecord>>(
      `/admin/management/exams/users/${userId}`,
      input,
    ),
    '考试安排保存失败',
  )
}

export async function updateAdminExam(
  userId: string,
  examId: string,
  input: ExamInput,
): Promise<ExamRecord> {
  return dataOrThrow(
    await authenticatedHttp.put<ApiResponse<ExamRecord>>(
      `/admin/management/exams/users/${userId}/${examId}`,
      input,
    ),
    '考试安排更新失败',
  )
}

export async function deleteAdminExam(userId: string, examId: string): Promise<void> {
  await authenticatedHttp.delete(`/admin/management/exams/users/${userId}/${examId}`)
}

export async function fetchAdminExams(userId: string): Promise<ExamRecord[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<ExamRecord[]>>(
      `/admin/management/exams/users/${userId}`,
    ),
    '考试安排加载失败',
  )
}
