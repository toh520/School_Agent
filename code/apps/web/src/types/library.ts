export interface LibraryBook {
  id: string
  holdingId: string
  code: string
  name: string
  isbn: string
  authors: string[]
  publisher: string
  edition: string
  publishedYear: number | null
  language: string
  category: string
  tags: string[]
  summary: string
  coverImage: string
  callNumber: string
  location: string
  totalCount: number
  availableCount: number
  available: boolean
}

export interface LibraryLoan {
  id: string
  bookId: string
  bookName: string
  coverImage: string
  authors: string
  callNumber: string
  location: string
  status: 'BORROWED' | 'RETURNED'
  borrowedAt: string
  returnedAt: string | null
}

export interface LibraryRecommendation {
  key: string
  sourceType: 'LIBRARY' | 'EXTERNAL'
  score: number
  featured: boolean
  reason: string
  bookId: string | null
  name: string
  isbn: string
  authors: string[]
  publisher: string
  publishedYear: number | null
  language: string
  category: string
  tags: string[]
  summary: string
  coverImage: string
  externalUrl: string
  queriedAt: string | null
}

export type LibraryBookInput = Omit<LibraryBook, 'id' | 'holdingId' | 'code' | 'available'>
