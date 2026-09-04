export type LearningMode = 'EXPLAIN' | 'SOLVE' | 'DIAGNOSE' | 'CORRECT'

export interface LearningSource {
  materialId: string
  fileName: string
  locator: string
}

export interface LearningAnswer {
  mode: LearningMode
  course: string
  answer: string
  steps: string[]
  conclusion: string
  diagnosis: string[]
  correctedPoints: string[]
  verification: string
  validationStatus: string
  sources: LearningSource[]
  limitations: string[]
}

export interface AttachmentView {
  id: string
  originalName: string
  mediaType: string
  parseStatus: 'READY' | 'FAILED'
  extractedPreview: string
}

export interface PracticeItem {
  id: string
  course: string
  knowledgePoint: string
  questionType: string
  difficulty: string
  prompt: string
  standardAnswer: string
  stepAnalysis: string
  testCases: Array<{ input: string; expectedOutput: string }>
  sourceType: string
  sourceLabel: string
  validationStatus: string
}

export interface PracticeAttempt {
  id: string
  practiceId: string
  correct: boolean
  score: number
  diagnosis: string[]
  causeType: string
  correctedConclusion: string
  reviewSuggestion: string
}

export interface ReviewPlan {
  id: string | null
  title: string
  priorityExplanation: string
  totalMinutes: number
  stages: Array<{
    examId: string
    name: string
    subject: string
    content: string
    objective: string
    suggestedMinutes: number
  }>
  assumptions: string[]
  limitations: string[]
}

export interface LearningOverview {
  attempts?: Array<Record<string, unknown>>
  activities: Array<Record<string, unknown>>
  mistakes: Array<Record<string, unknown>>
  mastery: Array<Record<string, unknown>>
  practices: Array<Record<string, unknown>>
}
