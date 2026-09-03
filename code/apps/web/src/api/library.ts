import type { ApiResponse } from '../types/api'
import type {
  LibraryBook,
  LibraryBookInput,
  LibraryLoan,
  LibraryRecommendation,
} from '../types/library'
import { agentHttp, authenticatedHttp } from './http'

function dataOrThrow<T>(response: { data: ApiResponse<T> }, message: string): T {
  if (response.data.data === null) throw new Error(message)
  return response.data.data
}

export async function fetchLibraryBooks(query = ''): Promise<LibraryBook[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<LibraryBook[]>>('/library/books', {
      params: { query: query || undefined },
    }),
    '馆藏加载失败',
  )
}

export async function fetchLibraryLoans(): Promise<LibraryLoan[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<LibraryLoan[]>>('/library/loans'),
    '借阅记录加载失败',
  )
}

export async function borrowLibraryBook(bookId: string): Promise<LibraryLoan> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<LibraryLoan>>(`/library/books/${bookId}/borrow`),
    '借阅失败',
  )
}

export async function returnLibraryLoan(loanId: string): Promise<LibraryLoan> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<LibraryLoan>>(`/library/loans/${loanId}/return`),
    '归还失败',
  )
}

export async function recommendLibraryBooks(
  requirement: string,
  books: LibraryBook[],
): Promise<LibraryRecommendation[]> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<LibraryRecommendation[]>>(
      '/library/recommendations',
      { requirement, books },
      { timeout: 0 },
    ),
    '推荐生成失败',
  )
}

export async function fetchAdminLibraryBooks(query = ''): Promise<LibraryBook[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<LibraryBook[]>>('/admin/library/books', {
      params: { query: query || undefined },
    }),
    '图书加载失败',
  )
}

export async function createAdminLibraryBook(input: LibraryBookInput): Promise<LibraryBook> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<LibraryBook>>('/admin/library/books', input),
    '图书创建失败',
  )
}

export async function updateAdminLibraryBook(
  bookId: string,
  input: LibraryBookInput,
): Promise<LibraryBook> {
  return dataOrThrow(
    await authenticatedHttp.put<ApiResponse<LibraryBook>>(`/admin/library/books/${bookId}`, input),
    '图书更新失败',
  )
}

export async function deactivateAdminLibraryBook(bookId: string): Promise<void> {
  await authenticatedHttp.delete(`/admin/library/books/${bookId}`)
}
