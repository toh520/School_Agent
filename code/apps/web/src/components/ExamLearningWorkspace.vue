<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  askLearningAssistant,
  deleteReviewPlan,
  evaluatePractice,
  fetchLearningOverview,
  fetchReviewPlans,
  generatePractices,
  generateReviewPlan,
  uploadLearningAttachment,
} from '../api/learning'
import type { ExamRecord } from '../types/exam'
import type { MeData } from '../types/identity'
import type {
  AttachmentView,
  LearningAnswer,
  LearningMode,
  LearningOverview,
  PracticeAttempt,
  PracticeItem,
  ReviewPlan,
} from '../types/learning'

const props = defineProps<{ exams: ExamRecord[]; me: MeData }>()

const courses = ['数据结构', '算法设计与分析', '计算机网络']
const section = ref<'assistant' | 'practice' | 'records' | 'plan'>('assistant')
const mode = ref<LearningMode>('EXPLAIN')
const course = ref(courses[0])
const prompt = ref('')
const workProcess = ref('')
const correction = ref('')
const attachments = ref<AttachmentView[]>([])
const uploading = ref(false)
const answering = ref(false)
const answer = ref<LearningAnswer | null>(null)
const history = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
let discussionVersion = 0

function resetDiscussion(): void {
  discussionVersion += 1
  history.value = []
  answer.value = null
  correction.value = ''
  prompt.value = ''
  workProcess.value = ''
  attachments.value = []
}

watch(course, resetDiscussion)

const practiceForm = reactive({
  knowledgePoint: '',
  questionTypes: ['CHOICE'] as string[],
  difficulty: 'MEDIUM',
  count: 3,
})
const generatingPractice = ref(false)
const practices = ref<PracticeItem[]>([])
const selectedPractice = ref<PracticeItem | null>(null)
const attemptProcess = ref('')
const attemptAnswer = ref('')
const evaluating = ref(false)
const evaluation = ref<PracticeAttempt | null>(null)
const overview = ref<LearningOverview | null>(null)
const loadingRecords = ref(false)

const selectedExamIds = ref<string[]>([])
const planMinutes = ref(600)
const planGoal = ref('掌握主要知识点和常见题型')
const planPreference = ref('')
const planInputs = reactive<Record<string, { difficulty: number; mastery: number; scope: string }>>(
  {},
)
const planning = ref(false)
const plan = ref<ReviewPlan | null>(null)
const savedPlans = ref<Array<Record<string, unknown>>>([])

const canUseMastery = computed(() => props.me.authorizations.MASTERY.granted)
const canUseExams = computed(() => props.me.authorizations.EXAMS.granted)

function switchSection(value: typeof section.value): void {
  section.value = value
  if (value === 'records') void loadRecords()
  if (value === 'plan') void loadPlans()
}

async function handleFiles(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const remaining = Math.max(0, 5 - attachments.value.length)
  const files = [...(input.files ?? [])].slice(0, remaining)
  if ((input.files?.length ?? 0) > remaining) ElMessage.warning('每个话题最多添加5个附件')
  if (!files.length) return
  const uploadVersion = discussionVersion
  uploading.value = true
  try {
    for (const file of files) {
      const uploaded = await uploadLearningAttachment(file)
      if (uploadVersion !== discussionVersion) break
      attachments.value.push(uploaded)
      if (uploaded.parseStatus === 'FAILED') ElMessage.warning(`${file.name} 未识别到可用文字`)
    }
  } catch {
    ElMessage.error('附件上传或解析失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function submitQuestion(requestMode = mode.value): Promise<void> {
  if (answering.value) return
  if (prompt.value.trim().length < 2) {
    ElMessage.warning('请输入想要学习或解析的内容')
    return
  }
  if (requestMode === 'DIAGNOSE' && workProcess.value.trim().length < 5) {
    ElMessage.warning('请提供完整作答过程')
    return
  }
  if (requestMode === 'CORRECT' && correction.value.trim().length < 2) {
    ElMessage.warning('请说明你认为需要纠正的地方')
    return
  }
  answering.value = true
  const requestVersion = discussionVersion
  const submittedProcess = workProcess.value.trim()
  const userTurn = requestMode === 'CORRECT' ? correction.value.trim() : prompt.value.trim()
  try {
    const result = await askLearningAssistant({
      mode: requestMode,
      course: course.value,
      prompt: prompt.value.trim(),
      workProcess: submittedProcess,
      previousAnswer: requestMode === 'CORRECT' ? JSON.stringify(answer.value) : '',
      correction: requestMode === 'CORRECT' ? correction.value.trim() : '',
      history: history.value,
      attachmentIds: attachments.value
        .filter((item) => item.parseStatus === 'READY')
        .map((item) => item.id),
    })
    // A course switch while a request is running must not contaminate its new discussion.
    if (discussionVersion !== requestVersion) return
    answer.value = result
    history.value.push(
      { role: 'user', content: `${userTurn}\n${submittedProcess}`.slice(0, 6000) },
      {
        role: 'assistant',
        content: JSON.stringify({
          answer: result.answer,
          steps: result.steps,
          conclusion: result.conclusion,
          correctedPoints: result.correctedPoints,
        }).slice(0, 6000),
      },
    )
    // Preserve the initial problem and the five most recent exchanges.
    if (history.value.length > 12)
      history.value = [...history.value.slice(0, 2), ...history.value.slice(-10)]
    if (requestMode === 'CORRECT') correction.value = ''
  } catch {
    ElMessage.error('AI 学习助手暂时不可用，已有考试和学习记录不受影响')
  } finally {
    answering.value = false
  }
}

async function createPracticeSet(): Promise<void> {
  if (!canUseMastery.value) {
    ElMessage.warning('请先在个人中心开启“掌握情况”授权')
    return
  }
  if (!practiceForm.knowledgePoint.trim()) {
    ElMessage.warning('请输入练习知识点')
    return
  }
  generatingPractice.value = true
  try {
    practices.value = await generatePractices({
      course: course.value,
      knowledgePoint: practiceForm.knowledgePoint.trim(),
      questionTypes: practiceForm.questionTypes,
      difficulty: practiceForm.difficulty,
      count: practiceForm.count,
    })
    selectedPractice.value = null
    evaluation.value = null
  } catch {
    ElMessage.error('练习生成失败，请检查数据授权或稍后重试')
  } finally {
    generatingPractice.value = false
  }
}

function startAttempt(item: PracticeItem): void {
  selectedPractice.value = item
  attemptProcess.value = ''
  attemptAnswer.value = ''
  evaluation.value = null
}

async function submitAttempt(): Promise<void> {
  if (!selectedPractice.value || attemptProcess.value.trim().length < 5) {
    ElMessage.warning('请写下完整作答过程')
    return
  }
  evaluating.value = true
  try {
    evaluation.value = await evaluatePractice({
      practiceId: selectedPractice.value.id,
      workProcess: attemptProcess.value.trim(),
      finalAnswer: attemptAnswer.value.trim(),
    })
  } catch {
    ElMessage.error('作答评估失败，本次不会更新掌握度')
  } finally {
    evaluating.value = false
  }
}

async function loadRecords(): Promise<void> {
  if (!canUseMastery.value) return
  loadingRecords.value = true
  try {
    overview.value = await fetchLearningOverview()
  } catch {
    ElMessage.error('学习记录加载失败')
  } finally {
    loadingRecords.value = false
  }
}

function toggleExam(exam: ExamRecord): void {
  const index = selectedExamIds.value.indexOf(exam.id)
  if (index >= 0) selectedExamIds.value.splice(index, 1)
  else {
    selectedExamIds.value.push(exam.id)
    planInputs[exam.id] ??= { difficulty: 3, mastery: 50, scope: '本学期重点内容' }
  }
}

async function createPlan(): Promise<void> {
  if (!canUseExams.value) {
    ElMessage.warning('请先在个人中心开启“考试数据”授权')
    return
  }
  if (!selectedExamIds.value.length) {
    ElMessage.warning('请至少选择一场考试')
    return
  }
  planning.value = true
  try {
    plan.value = await generateReviewPlan({
      exams: props.exams
        .filter((exam) => selectedExamIds.value.includes(exam.id))
        .map((exam) => ({
          id: exam.id,
          subject: exam.subject,
          examDate: exam.examDate,
          ...planInputs[exam.id],
        })),
      totalMinutes: planMinutes.value,
      goal: planGoal.value,
      preference: planPreference.value,
    })
    await loadPlans()
    ElMessage.success('复习计划已生成并保存')
  } catch {
    ElMessage.error('AI 规划暂时不可用，已有计划和考试记录不受影响')
  } finally {
    planning.value = false
  }
}

async function loadPlans(): Promise<void> {
  try {
    savedPlans.value = await fetchReviewPlans()
  } catch {
    ElMessage.error('已保存计划加载失败')
  }
}

async function removePlan(item: Record<string, unknown>): Promise<void> {
  try {
    await deleteReviewPlan(String(item.id))
    await loadPlans()
    if (plan.value?.id === item.id) plan.value = null
    ElMessage.success('复习计划已删除')
  } catch {
    ElMessage.error('复习计划删除失败')
  }
}

function value(record: Record<string, unknown>, camel: string, snake: string): unknown {
  return record[camel] ?? record[snake]
}
</script>

<template>
  <section class="learning-workspace">
    <nav class="learning-subnav" aria-label="AI 学习功能">
      <button :class="{ active: section === 'assistant' }" @click="switchSection('assistant')">
        讲解与解析
      </button>
      <button :class="{ active: section === 'practice' }" @click="switchSection('practice')">
        个性化练习
      </button>
      <button :class="{ active: section === 'records' }" @click="switchSection('records')">
        错题与掌握度
      </button>
      <button :class="{ active: section === 'plan' }" @click="switchSection('plan')">
        阶段复习计划
      </button>
    </nav>

    <div v-if="section === 'assistant'" class="learning-columns">
      <section class="learning-input-card">
        <p class="panel-label">ASK · 主动学习</p>
        <h2>你现在卡在哪一步？</h2>
        <div class="learning-choice-row">
          <el-select v-model="course" aria-label="课程">
            <el-option v-for="item in courses" :key="item" :label="item" :value="item" />
          </el-select>
          <el-radio-group v-model="mode">
            <el-radio-button value="EXPLAIN">知识讲解</el-radio-button>
            <el-radio-button value="SOLVE">题目解析</el-radio-button>
            <el-radio-button value="DIAGNOSE">错因诊断</el-radio-button>
          </el-radio-group>
        </div>
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="5"
          maxlength="12000"
          show-word-limit
          placeholder="输入知识点或题目…"
        />
        <el-input
          v-if="mode === 'DIAGNOSE'"
          v-model="workProcess"
          type="textarea"
          :rows="5"
          maxlength="12000"
          placeholder="请完整写下你的每一步作答过程…"
        />
        <div class="attachment-row">
          <label :class="{ busy: uploading }">
            <input
              type="file"
              multiple
              accept="image/png,image/jpeg,.pdf,.doc,.docx"
              :disabled="uploading"
              @change="handleFiles"
            />
            {{ uploading ? '正在识别附件…' : '添加图片 / PDF / Word' }}
          </label>
          <span
            v-for="item in attachments"
            :key="item.id"
            :class="item.parseStatus.toLowerCase()"
            >{{ item.originalName }}</span
          >
        </div>
        <el-button type="primary" size="large" :loading="answering" @click="submitQuestion()"
          >开始{{ mode === 'EXPLAIN' ? '讲解' : mode === 'SOLVE' ? '解析' : '诊断' }}</el-button
        >
        <el-button :disabled="answering" @click="resetDiscussion">新话题</el-button>
      </section>

      <section class="learning-answer-card">
        <div v-if="answer">
          <header>
            <span>{{
              answer.validationStatus === 'MATERIAL_SUPPORTED' ? '资料支持' : '未完全验证'
            }}</span
            ><strong>{{ answer.course }}</strong>
          </header>
          <p class="answer-lead">{{ answer.answer }}</p>
          <ol v-if="answer.steps.length" class="answer-steps">
            <li v-for="step in answer.steps" :key="step">{{ step }}</li>
          </ol>
          <div v-if="answer.diagnosis.length" class="answer-diagnosis">
            <strong>错因诊断</strong>
            <p v-for="item in answer.diagnosis" :key="item">{{ item }}</p>
          </div>
          <div v-if="answer.correctedPoints.length" class="answer-corrections">
            <strong>本次修正</strong>
            <p v-for="item in answer.correctedPoints" :key="item">{{ item }}</p>
          </div>
          <blockquote>{{ answer.conclusion }}</blockquote>
          <p v-for="limitation in answer.limitations" :key="limitation">提示：{{ limitation }}</p>
          <footer>
            <span>验证：{{ answer.verification }}</span>
            <small v-if="answer.sources.length"
              >参考：{{
                answer.sources.map((item) => `${item.fileName}（${item.locator}）`).join('、')
              }}</small
            >
          </footer>
          <div class="correction-box">
            <el-input v-model="correction" placeholder="这里不对，或者请换一种讲法…" />
            <el-button :loading="answering" @click="submitQuestion('CORRECT')"
              >检查并重新讲解</el-button
            >
          </div>
        </div>
        <el-empty v-else description="回答会在这里按步骤展开" />
      </section>
    </div>

    <section v-else-if="section === 'practice'" class="learning-section-card">
      <header>
        <div>
          <p class="panel-label">PRACTICE</p>
          <h2>用一组题检查真正掌握的部分</h2>
        </div>
      </header>
      <div class="practice-builder">
        <el-select v-model="course"
          ><el-option v-for="item in courses" :key="item" :label="item" :value="item"
        /></el-select>
        <el-input v-model="practiceForm.knowledgePoint" placeholder="知识点，例如：二叉树遍历" />
        <el-select v-model="practiceForm.questionTypes" multiple collapse-tags placeholder="题型">
          <el-option label="选择" value="CHOICE" /><el-option label="填空" value="FILL" /><el-option
            label="计算"
            value="CALCULATION"
          /><el-option label="证明" value="PROOF" /><el-option
            label="程序设计"
            value="PROGRAMMING"
          />
        </el-select>
        <el-select v-model="practiceForm.difficulty"
          ><el-option label="基础" value="BASIC" /><el-option
            label="中等"
            value="MEDIUM" /><el-option label="较难" value="HARD"
        /></el-select>
        <el-input-number v-model="practiceForm.count" :min="1" :max="10" />
        <el-button type="primary" :loading="generatingPractice" @click="createPracticeSet"
          >生成练习</el-button
        >
      </div>
      <div class="practice-list">
        <article v-for="(item, index) in practices" :key="item.id">
          <header>
            <span>{{ index + 1 }} · {{ item.questionType }}</span
            ><small>{{ item.sourceLabel }}</small>
          </header>
          <p>{{ item.prompt }}</p>
          <el-button @click="startAttempt(item)">开始作答</el-button>
        </article>
      </div>
      <div v-if="selectedPractice" class="attempt-sheet">
        <h3>{{ selectedPractice.prompt }}</h3>
        <el-input
          v-model="attemptProcess"
          type="textarea"
          :rows="6"
          placeholder="必须写下完整作答过程…"
        />
        <el-input v-model="attemptAnswer" placeholder="最终答案" />
        <el-button type="primary" :loading="evaluating" @click="submitAttempt">提交诊断</el-button>
        <div v-if="evaluation" :class="['attempt-result', { correct: evaluation.correct }]">
          <strong>{{
            evaluation.correct ? '作答正确' : `需要修正 · ${evaluation.causeType}`
          }}</strong
          ><span>{{ evaluation.score }} 分</span>
          <p v-for="item in evaluation.diagnosis" :key="item">{{ item }}</p>
          <p>{{ evaluation.reviewSuggestion }}</p>
          <details>
            <summary>查看标准答案与解析</summary>
            <p><strong>标准答案：</strong>{{ selectedPractice.standardAnswer }}</p>
            <p><strong>步骤解析：</strong>{{ selectedPractice.stepAnalysis }}</p>
            <div v-if="selectedPractice.testCases?.length" class="exam-test-cases">
              <strong>测试样例：</strong>
              <p v-for="(testCase, index) in selectedPractice.testCases" :key="index">
                {{ index + 1 }}. 输入：{{ testCase.input }}；预期输出：{{ testCase.expectedOutput }}
              </p>
            </div>
          </details>
        </div>
      </div>
    </section>

    <section
      v-else-if="section === 'records'"
      v-loading="loadingRecords"
      class="learning-section-card"
    >
      <div v-if="!canUseMastery" class="permission-note">
        开启“掌握情况”授权后，才会读取和分析你的练习记录。
      </div>
      <template v-else-if="overview">
        <header>
          <div>
            <p class="panel-label">LEARNING RECORD</p>
            <h2>薄弱点不是标签，而是下一次复习的起点</h2>
          </div>
        </header>
        <div class="mastery-grid">
          <article
            v-for="item in overview.mastery"
            :key="String(value(item, 'knowledgePoint', 'knowledge_point'))"
          >
            <span>{{ value(item, 'course', 'course') }}</span
            ><strong>{{ value(item, 'knowledgePoint', 'knowledge_point') }}</strong>
            <el-progress
              :percentage="Number(value(item, 'masteryScore', 'mastery_score') ?? 0)"
              :stroke-width="7"
            />
          </article>
        </div>
        <h3>错题本</h3>
        <div class="mistake-list">
          <article v-for="item in overview.mistakes" :key="String(item.id)">
            <strong>{{ value(item, 'knowledgePoint', 'knowledge_point') }}</strong
            ><span>{{ value(item, 'causeType', 'cause_type') }}</span>
            <p>{{ value(item, 'reviewSuggestion', 'review_suggestion') }}</p>
          </article>
        </div>
        <h3>历次作答（最近100条）</h3>
        <div class="activity-list">
          <details v-for="item in overview.attempts ?? []" :key="String(item.id)">
            <summary>
              {{ item.course }} · {{ item.score }}分 · {{ item.correct ? '正确' : '需要修正' }} ·
              {{ value(item, 'createdAt', 'created_at') }}
            </summary>
            <p><strong>题目：</strong>{{ item.prompt }}</p>
            <p style="white-space: pre-wrap">
              <strong>我的过程：</strong>{{ value(item, 'workProcess', 'work_process') }}
            </p>
            <p><strong>我的答案：</strong>{{ value(item, 'finalAnswer', 'final_answer') }}</p>
            <p style="white-space: pre-wrap">
              <strong>标准答案：</strong>{{ value(item, 'standardAnswer', 'standard_answer') }}
            </p>
            <p style="white-space: pre-wrap">
              <strong>步骤解析：</strong>{{ value(item, 'stepAnalysis', 'step_analysis') }}
            </p>
            <p v-for="entry in (item.diagnosis as { items?: string[] })?.items ?? []" :key="entry">
              {{ entry }}
            </p>
            <p>{{ (item.diagnosis as { reviewSuggestion?: string })?.reviewSuggestion }}</p>
            <p>来源：{{ value(item, 'sourceLabel', 'source_label') }}</p>
          </details>
        </div>
        <h3>学习活动</h3>
        <div class="activity-list">
          <article v-for="item in overview.activities" :key="String(item.id)">
            <span>{{ value(item, 'activityType', 'activity_type') }}</span>
            <strong>{{ value(item, 'course', 'course') }}</strong>
            <p>{{ value(item, 'summary', 'summary') }}</p>
          </article>
        </div>
      </template>
      <el-empty v-else description="暂无学习记录" />
    </section>

    <section v-else class="learning-section-card plan-builder">
      <header>
        <div>
          <p class="panel-label">STAGED PLAN</p>
          <h2>把有限时间分配给最需要的考试</h2>
        </div>
      </header>
      <div v-if="!canUseExams" class="permission-note">
        开启“考试数据”授权后，AI 才能读取你选中的考试。
      </div>
      <div class="plan-exam-list">
        <article
          v-for="exam in exams"
          :key="exam.id"
          :class="{ selected: selectedExamIds.includes(exam.id) }"
        >
          <button type="button" @click="toggleExam(exam)">
            <strong>{{ exam.subject }}</strong
            ><span>{{ exam.examDate }} · {{ exam.location }}</span>
          </button>
          <div v-if="selectedExamIds.includes(exam.id)" class="plan-exam-fields">
            <label>难度 <el-rate v-model="planInputs[exam.id].difficulty" /></label>
            <label>当前掌握度 <el-slider v-model="planInputs[exam.id].mastery" /></label>
            <el-input v-model="planInputs[exam.id].scope" placeholder="复习范围" />
          </div>
        </article>
      </div>
      <div class="plan-global-fields">
        <el-input-number v-model="planMinutes" :min="30" :max="100000" :step="30" /><span
          >分钟可用</span
        >
        <el-input v-model="planGoal" placeholder="复习目标" />
        <el-input v-model="planPreference" placeholder="复习偏好（可选）" />
        <el-button type="primary" :loading="planning" @click="createPlan">生成并保存计划</el-button>
      </div>
      <article v-if="plan" class="generated-plan">
        <header>
          <h3>{{ plan.title }}</h3>
          <span>共 {{ plan.totalMinutes }} 分钟</span>
        </header>
        <p>{{ plan.priorityExplanation }}</p>
        <ol>
          <li v-for="stage in plan.stages" :key="`${stage.examId}-${stage.name}`">
            <strong>{{ stage.name }} · {{ stage.subject }}</strong
            ><span>{{ stage.content }}</span
            ><small>{{ stage.objective }} · {{ stage.suggestedMinutes }} 分钟</small>
          </li>
        </ol>
        <footer>{{ plan.limitations.join('；') }}</footer>
      </article>
      <div v-if="savedPlans.length" class="saved-plan-list">
        <h3>已保存计划</h3>
        <article v-for="item in savedPlans" :key="String(item.id)">
          <div>
            <strong>{{ value(item, 'title', 'title') }}</strong>
            <span>{{ value(item, 'totalMinutes', 'total_minutes') }} 分钟</span>
          </div>
          <p>{{ value(item, 'priorityExplanation', 'priority_explanation') }}</p>
          <el-button text type="danger" @click="removePlan(item)">删除</el-button>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.learning-workspace {
  margin-top: 28px;
}
.learning-subnav {
  display: flex;
  gap: 6px;
  margin-bottom: 18px;
  padding: 6px;
  overflow-x: auto;
  border: 1px solid #d9d5c8;
  border-radius: 12px;
  background: #f7f5ef;
}
.learning-subnav button {
  flex: 1;
  min-width: 130px;
  padding: 12px 16px;
  border: 0;
  border-radius: 8px;
  color: #667782;
  background: transparent;
  cursor: pointer;
}
.learning-subnav button.active {
  color: #28343d;
  background: white;
  box-shadow: 0 5px 18px rgb(42 47 48 / 8%);
  font-weight: 700;
}
.learning-columns {
  display: grid;
  grid-template-columns: minmax(320px, 0.82fr) minmax(380px, 1.18fr);
  gap: 18px;
}
.learning-input-card,
.learning-answer-card,
.learning-section-card {
  padding: clamp(22px, 4vw, 36px);
  border: 1px solid #d9d5c8;
  border-radius: 12px;
  background: rgb(255 255 255 / 94%);
  box-shadow: 0 14px 36px rgb(50 45 30 / 6%);
}
.learning-input-card h2,
.learning-section-card h2 {
  margin: 8px 0 24px;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 27px;
  font-weight: 500;
}
.learning-input-card {
  display: grid;
  align-content: start;
  gap: 16px;
}
.learning-choice-row {
  display: grid;
  gap: 10px;
}
.attachment-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.attachment-row label {
  padding: 8px 12px;
  border: 1px dashed #c9912f;
  border-radius: 6px;
  color: #77571c;
  cursor: pointer;
}
.attachment-row input {
  display: none;
}
.attachment-row span {
  max-width: 170px;
  padding: 6px 9px;
  overflow: hidden;
  border-radius: 5px;
  background: #eef4ef;
  color: #4c6753;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.attachment-row span.failed {
  color: #9d4d44;
  background: #fff0ed;
}
.learning-answer-card {
  min-height: 520px;
}
.learning-answer-card header,
.practice-list header,
.generated-plan header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #71808a;
  font-size: 11px;
}
.learning-answer-card header span {
  color: #6b571f;
}
.answer-lead {
  margin: 28px 0;
  color: #28343d;
  font-size: 17px;
  line-height: 1.85;
}
.answer-steps {
  display: grid;
  gap: 12px;
  padding-left: 26px;
  color: #465a65;
  line-height: 1.75;
}
.learning-answer-card blockquote {
  margin: 28px 0;
  padding: 18px 21px;
  border-left: 4px solid #c9912f;
  background: #fbf7ec;
  color: #28343d;
  font-weight: 700;
}
.learning-answer-card footer {
  display: grid;
  gap: 6px;
  color: #71808a;
  font-size: 11px;
}
.answer-diagnosis,
.answer-corrections {
  margin-top: 20px;
  padding: 16px;
  border-radius: 8px;
  background: #f4f6f5;
  color: #465a65;
}
.answer-diagnosis p,
.answer-corrections p {
  margin: 7px 0 0;
}
.correction-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin-top: 25px;
}
.practice-builder {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.2fr 1fr auto auto;
  gap: 10px;
}
.practice-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
}
.practice-list article,
.mistake-list article,
.mastery-grid article {
  padding: 18px;
  border: 1px solid #e0ddd4;
  border-radius: 9px;
}
.practice-list p {
  min-height: 75px;
  color: #394c56;
  line-height: 1.65;
}
.attempt-sheet {
  display: grid;
  gap: 13px;
  margin-top: 22px;
  padding: 24px;
  border: 1px solid #c9912f;
  border-radius: 10px;
  background: #fffdf7;
}
.attempt-result {
  padding: 16px;
  border-left: 4px solid #bd5b4d;
  background: #fff3f0;
}
.attempt-result.correct {
  border-color: #4f8562;
  background: #f0f7f2;
}
.attempt-result span {
  margin-left: 15px;
}
.permission-note {
  padding: 18px;
  border: 1px dashed #c9912f;
  border-radius: 8px;
  color: #715723;
  background: #fffaf0;
}
.mastery-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0 30px;
}
.mastery-grid article {
  display: grid;
  gap: 10px;
}
.mastery-grid span {
  color: #71808a;
  font-size: 11px;
}
.mistake-list {
  display: grid;
  gap: 10px;
}
.activity-list,
.saved-plan-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}
.activity-list article,
.saved-plan-list article {
  padding: 16px 18px;
  border-top: 1px solid #d9d5c8;
}
.activity-list span,
.saved-plan-list span {
  margin-right: 12px;
  color: #8b6b2d;
  font-size: 11px;
}
.activity-list p,
.saved-plan-list p {
  margin: 7px 0 0;
  color: #71808a;
}
.saved-plan-list article {
  display: grid;
  grid-template-columns: 1fr auto;
}
.saved-plan-list article p {
  grid-column: 1;
}
.saved-plan-list article .el-button {
  grid-row: 1 / span 2;
  grid-column: 2;
}
.mistake-list article {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px 20px;
}
.mistake-list p {
  grid-column: 1 / -1;
  margin: 0;
  color: #71808a;
}
.plan-exam-list {
  display: grid;
  gap: 10px;
}
.plan-exam-list article {
  border: 1px solid #d9d5c8;
  border-radius: 9px;
}
.plan-exam-list article.selected {
  border-color: #c9912f;
}
.plan-exam-list button {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 17px;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.plan-exam-list button span {
  color: #71808a;
}
.plan-exam-fields {
  display: grid;
  grid-template-columns: 1fr 1.5fr 2fr;
  gap: 18px;
  padding: 0 17px 17px;
}
.plan-exam-fields label {
  color: #71808a;
  font-size: 11px;
}
.plan-global-fields {
  display: grid;
  grid-template-columns: auto auto 1fr 1fr auto;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
}
.generated-plan {
  margin-top: 26px;
  padding: 25px;
  border: 1px solid #c9912f;
  border-radius: 10px;
  background: #fffdf7;
}
.generated-plan h3 {
  margin: 0;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 24px;
}
.generated-plan ol {
  display: grid;
  gap: 12px;
  padding-left: 22px;
}
.generated-plan li {
  padding: 12px;
}
.generated-plan li span,
.generated-plan li small {
  display: block;
  margin-top: 6px;
  color: #71808a;
}
.generated-plan footer {
  padding-top: 14px;
  border-top: 1px dashed #d9d5c8;
  color: #806832;
  font-size: 12px;
}
@media (max-width: 960px) {
  .learning-columns,
  .practice-builder,
  .plan-global-fields {
    grid-template-columns: 1fr;
  }
  .practice-list,
  .mastery-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .practice-list,
  .mastery-grid,
  .plan-exam-fields {
    grid-template-columns: 1fr;
  }
  .correction-box {
    grid-template-columns: 1fr;
  }
}
</style>
