export type LearningMode = 'EXPLAIN' | 'SOLVE' | 'DIAGNOSE' | 'CORRECT'

export interface LearningSource {
  materialId: string
  fileName: string
  locator: string
  snippet: string
}

export interface LearningClaim {
  text: string
  origin: 'COURSE_MATERIAL' | 'USER_ATTACHMENT' | 'AI_SUPPLEMENT'
  sources: LearningSource[]
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
  prerequisiteKnowledge: string[]
  keyConcepts: string[]
  keyClaims: LearningClaim[]
  workedExample: string
  commonMistakes: string[]
  memoryTip: string
  selfTestQuestion: string
  selfTestAnswer: string
  evidenceConflicts: string[]
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

export interface LearningOverview {
  attempts?: Array<Record<string, unknown>>
  activities: Array<Record<string, unknown>>
  mistakes: Array<Record<string, unknown>>
  practices: Array<Record<string, unknown>>
  mastery: Array<Record<string, unknown>>
  weakPoints: Array<Record<string, unknown>>
}

export interface ReviewPlanStage {
  id: string
  stageIndex: number
  name: string
  phase: 'FOUNDATION' | 'PRACTICE' | 'SPRINT'
  startDate: string
  endDate: string
  subject: string
  knowledgePoints: string[]
  objective: string
  suggestedMinutes: number
  method: string
  rationale: string
}

export interface ReviewPlanExam {
  id: string
  subject: string
  examDate: string
  startTime: string
  location: string
  priorityScore: number
  allocatedMinutes: number
}

export interface ReviewPlan {
  id: string
  planGroupId: string
  versionNumber: number
  isCurrent: boolean
  title: string
  status: string
  target: string
  constraints: string
  inputSnapshot: Record<string, unknown>
  priorityExplanation: string
  assumptions: string[]
  limitations: string[]
  totalMinutes: number
  modelName: string | null
  dataAsOf: string
  createdAt: string
  stale: boolean
  exams: ReviewPlanExam[]
  stages: ReviewPlanStage[]
}
