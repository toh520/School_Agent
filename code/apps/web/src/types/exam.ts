export interface ExamRecord {
  id: string
  subject: string
  examDate: string
  startTime: string
  endTime: string
  location: string
  createdAt: string
  updatedAt: string
}

export interface ExamInput {
  subject: string
  examDate: string
  startTime: string
  endTime: string
  location: string
}
