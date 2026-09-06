<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  evaluatePractice,
  fetchLearningOverview,
  generatePractices,
  setMistakeMastery,
} from '../api/learning'
import type { ExamRecord } from '../types/exam'
import type { MeData } from '../types/identity'
import type { LearningOverview, PracticeAttempt, PracticeItem } from '../types/learning'
import LearningExplanationPanel from './LearningExplanationPanel.vue'
import ReviewPlanWorkspace from './ReviewPlanWorkspace.vue'

const props = defineProps<{ me: MeData; exams: ExamRecord[] }>()

const courses = ['数据结构', '算法设计与分析', '计算机网络']
const section = ref<'assistant' | 'practice' | 'records' | 'plans'>('assistant')
const course = ref(courses[0])

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

// Keep the persisted MASTERY scope key for backward-compatible consent records;
// the product surface now uses it only for practice and mistake-notebook storage.
const canUseMistakes = computed(() => props.me.authorizations.MASTERY.granted)

function switchSection(value: typeof section.value): void {
  section.value = value
  if (value === 'records') void loadRecords()
}

async function createPracticeSet(): Promise<void> {
  if (!canUseMistakes.value) {
    ElMessage.warning('请先在个人中心开启“练习与错题记录”授权')
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
    ElMessage.error('作答评估失败，本次不会写入错题本')
  } finally {
    evaluating.value = false
  }
}

async function loadRecords(): Promise<void> {
  if (!canUseMistakes.value) return
  loadingRecords.value = true
  try {
    const result = await fetchLearningOverview()
    overview.value = {
      ...result,
      mastery: result.mastery ?? [],
      weakPoints: result.weakPoints ?? [],
    }
  } catch {
    ElMessage.error('错题本加载失败')
  } finally {
    loadingRecords.value = false
  }
}

async function markMastered(item: Record<string, unknown>, mastered: boolean): Promise<void> {
  try {
    await setMistakeMastery(String(item.id), mastered)
    await loadRecords()
    ElMessage.success(mastered ? '已移入掌握记录' : '已恢复为待复习错题')
  } catch {
    ElMessage.error('错题状态更新失败')
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
        错题本
      </button>
      <button :class="{ active: section === 'plans' }" @click="switchSection('plans')">
        复习计划
      </button>
    </nav>

    <LearningExplanationPanel v-if="section === 'assistant'" />

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
      <div v-if="!canUseMistakes" class="permission-note">
        开启“练习与错题记录”授权后，才会读取你的错题本。
      </div>
      <template v-else-if="overview">
        <header class="notebook-heading">
          <div>
            <p class="panel-label">MISTAKE NOTEBOOK · 错题复盘档案</p>
            <h2>把错误完整留下，下一次才知道从哪里改起</h2>
            <p>共 {{ overview.mistakes.length }} 道错题，保存原题、作答、错因与可核验解析。</p>
          </div>
        </header>
        <section v-if="overview.weakPoints.length" class="weak-point-board">
          <header>
            <strong>高频薄弱点</strong>
            <span>按未掌握错题次数排序</span>
          </header>
          <div>
            <article
              v-for="point in overview.weakPoints"
              :key="`${point.course}-${point.knowledge_point}`"
            >
              <strong>{{ point.knowledge_point }}</strong>
              <span>{{ point.course }} · {{ point.mistake_count }} 次错误</span>
              <small
                >掌握度 {{ Math.round(Number(point.mastery_score)) }}% ·
                {{ (point.causes as string[]).join('、') }}</small
              >
            </article>
          </div>
        </section>
        <el-empty v-if="!overview.mistakes.length" description="还没有错题记录" />
        <div v-else class="mistake-notebook">
          <article
            v-for="(item, index) in overview.mistakes"
            :key="String(item.id)"
            class="mistake-sheet"
          >
            <header>
              <span class="mistake-number">{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <p>
                  {{ value(item, 'course', 'course') }} ·
                  {{ value(item, 'knowledgePoint', 'knowledge_point') }}
                </p>
                <h3>{{ value(item, 'prompt', 'prompt') }}</h3>
              </div>
              <span class="mistake-score">{{ value(item, 'score', 'score') }} 分</span>
            </header>
            <div class="mistake-meta">
              <span>{{ value(item, 'questionType', 'question_type') }}</span>
              <span>错因：{{ value(item, 'causeType', 'cause_type') }}</span>
              <span>{{ value(item, 'createdAt', 'created_at') }}</span>
            </div>
            <div class="mistake-review-grid">
              <section class="mistake-user-answer">
                <h4>我的作答过程</h4>
                <p>{{ value(item, 'workProcess', 'work_process') || '未填写' }}</p>
                <h4>我的最终答案</h4>
                <p>{{ value(item, 'finalAnswer', 'final_answer') || '未填写' }}</p>
              </section>
              <section class="mistake-diagnosis">
                <h4>错误原因</h4>
                <ul>
                  <li
                    v-for="entry in (item.diagnosis as { items?: string[] })?.items ?? []"
                    :key="entry"
                  >
                    {{ entry }}
                  </li>
                </ul>
                <p>{{ value(item, 'correctedConclusion', 'corrected_conclusion') }}</p>
              </section>
            </div>
            <section class="mistake-correction">
              <h4>正确答案</h4>
              <p>{{ value(item, 'standardAnswer', 'standard_answer') }}</p>
              <h4>解题分析</h4>
              <p>{{ value(item, 'stepAnalysis', 'step_analysis') }}</p>
              <div
                v-if="
                  (value(item, 'testCases', 'test_cases') as Array<Record<string, unknown>>)?.length
                "
                class="exam-test-cases"
              >
                <h4>校验样例</h4>
                <p
                  v-for="(testCase, caseIndex) in value(item, 'testCases', 'test_cases') as Array<
                    Record<string, unknown>
                  >"
                  :key="caseIndex"
                >
                  {{ caseIndex + 1 }}. 输入：{{ testCase.input }}；预期输出：{{
                    testCase.expectedOutput
                  }}
                </p>
              </div>
            </section>
            <footer>
              <p>
                <strong>复习建议：</strong
                >{{ value(item, 'reviewSuggestion', 'review_suggestion') }}
              </p>
              <span
                >来源：{{ value(item, 'sourceLabel', 'source_label') }} ·
                {{ value(item, 'validationStatus', 'validation_status') }}</span
              >
              <el-button
                size="small"
                :type="value(item, 'mastered', 'mastered') ? 'default' : 'success'"
                plain
                @click="markMastered(item, !Boolean(value(item, 'mastered', 'mastered')))"
              >
                {{ value(item, 'mastered', 'mastered') ? '恢复待复习' : '标记已掌握' }}
              </el-button>
            </footer>
          </article>
        </div>
      </template>
      <el-empty v-else description="暂无错题记录" />
    </section>

    <ReviewPlanWorkspace v-else :exams="exams" :me="me" />
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
.learning-section-card {
  padding: clamp(22px, 4vw, 36px);
  border: 1px solid #d9d5c8;
  border-radius: 12px;
  background: rgb(255 255 255 / 94%);
  box-shadow: 0 14px 36px rgb(50 45 30 / 6%);
}
.learning-section-card h2 {
  margin: 8px 0 24px;
  font-family: Georgia, 'Microsoft YaHei', serif;
  font-size: 27px;
  font-weight: 500;
}
.practice-list header,
.generated-plan header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #71808a;
  font-size: 11px;
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
.practice-list article {
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
.notebook-heading {
  margin-bottom: 24px;
}
.notebook-heading p:last-child {
  color: #71808a;
}
.weak-point-board {
  margin-bottom: 24px;
  padding: 18px;
  border: 1px solid #d9d5c8;
  border-radius: 8px;
  background: #f7f5ef;
}
.weak-point-board > header {
  display: flex;
  justify-content: space-between;
  color: #52646e;
}
.weak-point-board > header span {
  color: #829096;
  font-size: 12px;
}
.weak-point-board > div {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.weak-point-board article {
  display: grid;
  gap: 5px;
  padding: 13px;
  border-left: 3px solid #bd5b4d;
  background: #fff;
}
.weak-point-board span,
.weak-point-board small {
  color: #71808a;
}
.mistake-notebook {
  display: grid;
  gap: 22px;
}
.mistake-sheet {
  overflow: hidden;
  border: 1px solid #d8d2c5;
  border-left: 5px solid #a8473d;
  border-radius: 8px;
  background: #fffef9;
  box-shadow: 0 10px 28px rgba(42, 49, 53, 0.07);
}
.mistake-sheet > header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: start;
  padding: 22px 24px 16px;
}
.mistake-number {
  color: #a8473d;
  font:
    700 24px Georgia,
    serif;
}
.mistake-sheet h3 {
  margin: 4px 0 0;
  line-height: 1.55;
  white-space: pre-wrap;
}
.mistake-sheet header p {
  margin: 0;
  color: #806832;
  font-size: 12px;
}
.mistake-score {
  padding: 5px 9px;
  color: #9c3f37;
  background: #fae9e5;
  border-radius: 4px;
  font-weight: 700;
}
.mistake-meta {
  display: flex;
  gap: 18px;
  padding: 10px 24px;
  border-block: 1px dashed #ddd5c6;
  color: #71808a;
  font-size: 12px;
}
.mistake-review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.mistake-review-grid section,
.mistake-correction {
  padding: 20px 24px;
}
.mistake-user-answer {
  background: #faf7f0;
}
.mistake-diagnosis {
  border-left: 1px solid #e3ddd1;
  background: #fff6f3;
}
.mistake-sheet h4 {
  margin: 0 0 8px;
  color: #33434c;
}
.mistake-sheet p {
  line-height: 1.7;
  white-space: pre-wrap;
}
.mistake-correction {
  border-top: 1px solid #e3ddd1;
}
.mistake-sheet > footer {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 24px;
  color: #6f6249;
  background: #f5f1e8;
}
.mistake-sheet > footer p {
  margin: 0;
}
.mistake-sheet > footer span {
  font-size: 11px;
  text-align: right;
}
@media (max-width: 960px) {
  .practice-builder,
  .mistake-review-grid {
    grid-template-columns: 1fr;
  }
  .practice-list {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .practice-list,
  .mistake-review-grid {
    grid-template-columns: 1fr;
  }
  .mistake-sheet > header {
    grid-template-columns: auto 1fr;
  }
  .mistake-score {
    grid-column: 2;
  }
  .mistake-sheet > footer {
    flex-direction: column;
  }
  .mistake-sheet > footer span {
    text-align: left;
  }
}
</style>
