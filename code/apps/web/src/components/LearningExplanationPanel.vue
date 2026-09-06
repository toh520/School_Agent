<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { askLearningAssistant, uploadLearningAttachment } from '../api/learning'
import { learningExamples } from '../learning-examples'
import type { AttachmentView, LearningAnswer, LearningMode } from '../types/learning'
import '../learning-explanation.css'

const courses = ['数据结构', '算法设计与分析', '计算机网络']
const course = ref(courses[0])
const mode = ref<Exclude<LearningMode, 'CORRECT'>>('EXPLAIN')
const learningGoal = ref<'QUICK' | 'EXAM' | 'DEEP'>('EXAM')
const familiarity = ref<'BEGINNER' | 'BASIC' | 'REVIEW'>('BASIC')
const prompt = ref('')
const workProcess = ref('')
const finalAnswer = ref('')
const confusion = ref('')
const correction = ref('')
const attachments = ref<AttachmentView[]>([])
const uploading = ref(false)
const answering = ref(false)
const answer = ref<LearningAnswer | null>(null)
const previousConclusion = ref('')
const history = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
const revealedSteps = ref(0)
const showFullSolution = ref(false)
const showFinalAnswer = ref(false)
let discussionVersion = 0

const modeCopy = computed(
  () =>
    ({
      EXPLAIN: {
        eyebrow: 'CONCEPT · 概念讲义',
        title: '把一个知识点真正讲明白',
        prompt: '输入知识点，例如：二叉树的层序遍历为什么需要队列',
        submit: '生成分层讲义',
      },
      SOLVE: {
        eyebrow: 'PROBLEM · 题目解析',
        title: '先给提示，再逐步展开解法',
        prompt: '粘贴完整题目，包含已知条件、问题和选项（如有）',
        submit: '准备分步解析',
      },
      DIAGNOSE: {
        eyebrow: 'DIAGNOSIS · 错因诊断',
        title: '定位从哪一步开始偏离',
        prompt: '粘贴原题，保留所有条件和题目要求',
        submit: '开始错因诊断',
      },
    })[mode.value],
)

const sampleQuestions = computed(() => learningExamples[course.value]?.[mode.value] ?? [])
const visibleSteps = computed(() => {
  if (!answer.value) return []
  return showFullSolution.value
    ? answer.value.steps
    : answer.value.steps.slice(0, revealedSteps.value)
})
const showLearningBody = computed(() => answer.value?.mode !== 'SOLVE' || showFullSolution.value)

type NumberedSection =
  | 'conclusion'
  | 'prerequisites'
  | 'concepts'
  | 'steps'
  | 'example'
  | 'mistakes'
  | 'selfTest'

const visibleNumberedSections = computed<NumberedSection[]>(() => {
  const current = answer.value
  if (!current) return []
  const sections: NumberedSection[] = ['conclusion']
  if (current.prerequisiteKnowledge.length) sections.push('prerequisites')
  if (current.keyConcepts.length) sections.push('concepts')
  if (current.steps.length) sections.push('steps')
  if (current.workedExample) sections.push('example')
  if (current.commonMistakes.length) sections.push('mistakes')
  if (current.selfTestQuestion) sections.push('selfTest')
  return sections
})

function sectionNumber(section: NumberedSection): string {
  const position = visibleNumberedSections.value.indexOf(section)
  return String(position < 0 ? 0 : position + 1).padStart(2, '0')
}

function resetDiscussion(): void {
  discussionVersion += 1
  prompt.value = ''
  workProcess.value = ''
  finalAnswer.value = ''
  confusion.value = ''
  correction.value = ''
  attachments.value = []
  answer.value = null
  previousConclusion.value = ''
  history.value = []
  resetReveal()
}

function resetReveal(): void {
  revealedSteps.value = 0
  showFullSolution.value = false
  showFinalAnswer.value = false
}

watch([course, mode], resetDiscussion)

function applyExample(value: string): void {
  prompt.value = value
}

async function handleFiles(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const remaining = Math.max(0, 5 - attachments.value.length)
  const files = [...(input.files ?? [])].slice(0, remaining)
  if ((input.files?.length ?? 0) > remaining) ElMessage.warning('每个话题最多添加 5 个附件')
  if (!files.length) {
    input.value = ''
    return
  }
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
    ElMessage.error('附件上传或解析失败，请检查文件格式和大小')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

function removeAttachment(id: string): void {
  attachments.value = attachments.value.filter((item) => item.id !== id)
}

function compactPreviousAnswer(): string {
  if (!answer.value) return ''
  return JSON.stringify({
    answer: answer.value.answer.slice(0, 1800),
    steps: answer.value.steps.slice(0, 8).map((item) => item.slice(0, 400)),
    conclusion: answer.value.conclusion.slice(0, 1200),
    diagnosis: answer.value.diagnosis.slice(0, 6).map((item) => item.slice(0, 300)),
    correctedPoints: answer.value.correctedPoints.slice(0, 6).map((item) => item.slice(0, 300)),
  })
}

function validateRequest(requestMode: LearningMode): boolean {
  if (prompt.value.trim().length < 2) {
    ElMessage.warning('请填写知识点或完整题目')
    return false
  }
  if (requestMode === 'DIAGNOSE' && workProcess.value.trim().length < 5) {
    ElMessage.warning('错因诊断需要完整作答过程，至少填写 5 个字符')
    return false
  }
  if (requestMode === 'CORRECT' && correction.value.trim().length < 2) {
    ElMessage.warning('请说明需要核对或修正的地方')
    return false
  }
  return true
}

async function submitQuestion(requestMode: LearningMode = mode.value): Promise<void> {
  if (answering.value || !validateRequest(requestMode)) return
  answering.value = true
  const requestVersion = discussionVersion
  const userTurn = requestMode === 'CORRECT' ? correction.value.trim() : prompt.value.trim()
  const oldConclusion = answer.value?.conclusion ?? ''
  try {
    const result = await askLearningAssistant({
      mode: requestMode,
      course: course.value,
      prompt: prompt.value.trim(),
      workProcess: workProcess.value.trim(),
      finalAnswer: finalAnswer.value.trim(),
      confusion: confusion.value.trim(),
      learningGoal: learningGoal.value,
      familiarity: familiarity.value,
      previousAnswer: requestMode === 'CORRECT' ? compactPreviousAnswer() : '',
      correction: requestMode === 'CORRECT' ? correction.value.trim() : '',
      history: history.value,
      attachmentIds: attachments.value
        .filter((item) => item.parseStatus === 'READY')
        .map((item) => item.id),
    })
    if (discussionVersion !== requestVersion) return
    previousConclusion.value = requestMode === 'CORRECT' ? oldConclusion : ''
    answer.value = result
    resetReveal()
    history.value.push(
      { role: 'user', content: `${userTurn}\n${workProcess.value}`.slice(0, 6000) },
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
    if (history.value.length > 12)
      history.value = [...history.value.slice(0, 2), ...history.value.slice(-10)]
    if (requestMode === 'CORRECT') correction.value = ''
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } }).response?.status
    ElMessage.error(
      status === 422
        ? '输入内容未通过校验，请检查题目和作答过程'
        : '学习助手暂时不可用，请稍后重试；已有学习记录不受影响',
    )
  } finally {
    answering.value = false
  }
}

function revealHint(): void {
  if (!answer.value) return
  revealedSteps.value = Math.min(revealedSteps.value + 1, answer.value.steps.length)
}

function revealSolution(): void {
  showFullSolution.value = true
}

function statusLabel(status: string): string {
  return (
    (
      {
        MATERIAL_SUPPORTED: '课程资料支持',
        PARTIAL: '部分资料支持',
        UNVERIFIED: '暂无课程资料',
        NEEDS_CLARIFICATION: '需要补充信息',
      } as Record<string, string>
    )[status] ?? '已完成校验'
  )
}

function originLabel(origin: string): string {
  return (
    (
      {
        COURSE_MATERIAL: '课程资料依据',
        USER_ATTACHMENT: '用户附件依据',
        AI_SUPPLEMENT: 'AI 补充',
      } as Record<string, string>
    )[origin] ?? 'AI 补充'
  )
}
</script>

<template>
  <div class="explanation-layout">
    <section class="question-sheet" aria-labelledby="question-sheet-title">
      <header class="sheet-heading">
        <p>{{ modeCopy.eyebrow }}</p>
        <h2 id="question-sheet-title">{{ modeCopy.title }}</h2>
      </header>

      <div class="field-block">
        <label>学习场景</label>
        <el-radio-group v-model="mode" aria-label="学习场景">
          <el-radio-button value="EXPLAIN">知识讲解</el-radio-button>
          <el-radio-button value="SOLVE">题目解析</el-radio-button>
          <el-radio-button value="DIAGNOSE">错因诊断</el-radio-button>
        </el-radio-group>
      </div>

      <div class="compact-fields">
        <div class="field-block">
          <label for="learning-course">课程</label>
          <el-select id="learning-course" v-model="course" aria-label="课程">
            <el-option v-for="item in courses" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
        <div class="field-block">
          <label for="learning-familiarity">当前基础</label>
          <el-select id="learning-familiarity" v-model="familiarity" aria-label="当前基础">
            <el-option label="刚开始接触" value="BEGINNER" />
            <el-option label="了解基本概念" value="BASIC" />
            <el-option label="正在复习巩固" value="REVIEW" />
          </el-select>
        </div>
      </div>

      <div class="field-block learning-goal">
        <label>本次目标</label>
        <div role="group" aria-label="本次目标">
          <button :class="{ active: learningGoal === 'QUICK' }" @click="learningGoal = 'QUICK'">
            快速理解
          </button>
          <button :class="{ active: learningGoal === 'EXAM' }" @click="learningGoal = 'EXAM'">
            考试复习
          </button>
          <button :class="{ active: learningGoal === 'DEEP' }" @click="learningGoal = 'DEEP'">
            深入掌握
          </button>
        </div>
      </div>

      <div class="field-block">
        <label for="learning-prompt">{{ mode === 'EXPLAIN' ? '知识点' : '原题' }}</label>
        <el-input
          id="learning-prompt"
          v-model="prompt"
          type="textarea"
          :rows="5"
          maxlength="12000"
          show-word-limit
          :placeholder="modeCopy.prompt"
        />
        <div class="sample-strip" aria-label="示例问题">
          <span>示例</span>
          <button v-for="item in sampleQuestions" :key="item" @click="applyExample(item)">
            {{ item }}
          </button>
        </div>
      </div>

      <div v-if="mode !== 'EXPLAIN'" class="field-block">
        <label for="learning-process">{{
          mode === 'DIAGNOSE' ? '完整作答过程（必填）' : '我的思路（选填）'
        }}</label>
        <el-input
          id="learning-process"
          v-model="workProcess"
          type="textarea"
          :rows="4"
          maxlength="12000"
          placeholder="按实际顺序写下每一步，不必整理成标准答案"
        />
      </div>
      <div v-if="mode !== 'EXPLAIN'" class="compact-fields">
        <div class="field-block">
          <label for="learning-final-answer">我的最终答案（选填）</label>
          <el-input
            id="learning-final-answer"
            v-model="finalAnswer"
            placeholder="填写你得到的答案"
          />
        </div>
        <div v-if="mode === 'DIAGNOSE'" class="field-block">
          <label for="learning-confusion">最困惑的位置（选填）</label>
          <el-input
            id="learning-confusion"
            v-model="confusion"
            placeholder="例如：第二步为什么不能这样变形"
          />
        </div>
      </div>

      <div class="attachment-area">
        <label :class="{ busy: uploading }">
          <input
            type="file"
            multiple
            accept="image/png,image/jpeg,.pdf,.doc,.docx"
            :disabled="uploading"
            @change="handleFiles"
          />
          {{ uploading ? '正在识别…' : '添加图片 / PDF / Word' }}
        </label>
        <article v-for="item in attachments" :key="item.id" :class="item.parseStatus.toLowerCase()">
          <span>{{ item.originalName }}</span>
          <small>{{ item.parseStatus === 'READY' ? '已提取文字' : '解析失败' }}</small>
          <button :aria-label="`移除 ${item.originalName}`" @click="removeAttachment(item.id)">
            ×
          </button>
        </article>
      </div>

      <div class="sheet-actions">
        <el-button type="primary" size="large" :loading="answering" @click="submitQuestion()">
          {{ modeCopy.submit }}
        </el-button>
        <el-button :disabled="answering" @click="resetDiscussion">新话题</el-button>
      </div>
    </section>

    <section class="lecture-sheet" aria-live="polite">
      <template v-if="answer">
        <header class="answer-header">
          <div>
            <span :class="['evidence-status', answer.validationStatus.toLowerCase()]">
              {{ statusLabel(answer.validationStatus) }}
            </span>
            <strong>{{ answer.course }}</strong>
          </div>
          <small>{{ answer.verification }}</small>
        </header>

        <div v-if="answer.mode === 'SOLVE' && !showFullSolution" class="hint-workspace">
          <p class="section-number">解析已准备好</p>
          <h3>先保留独立思考的机会</h3>
          <p>你可以一次查看一个提示，也可以直接展开完整解法。最终结论会单独保留。</p>
          <ol v-if="visibleSteps.length" class="layer-list">
            <li v-for="step in visibleSteps" :key="step">{{ step }}</li>
          </ol>
          <div>
            <el-button :disabled="revealedSteps >= answer.steps.length" @click="revealHint">
              {{ revealedSteps ? '再给一个提示' : '给我一个提示' }}
            </el-button>
            <el-button type="primary" plain @click="revealSolution">展开完整解法</el-button>
          </div>
        </div>

        <template v-if="showLearningBody">
          <section class="answer-lead-block">
            <span class="section-number">{{ sectionNumber('conclusion') }} · 一句话结论</span>
            <p>{{ answer.answer }}</p>
          </section>

          <div v-if="answer.prerequisiteKnowledge.length" class="answer-section">
            <h3>
              <span>{{ sectionNumber('prerequisites') }}</span
              >需要先知道
            </h3>
            <ul class="tag-list">
              <li v-for="item in answer.prerequisiteKnowledge" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div v-if="answer.keyConcepts.length" class="answer-section">
            <h3>
              <span>{{ sectionNumber('concepts') }}</span
              >核心概念
            </h3>
            <ul class="layer-list">
              <li v-for="item in answer.keyConcepts" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div v-if="answer.steps.length" class="answer-section">
            <h3>
              <span>{{ sectionNumber('steps') }}</span
              >{{ answer.mode === 'DIAGNOSE' ? '逐步核对' : '推导步骤' }}
            </h3>
            <ol class="layer-list">
              <li v-for="step in answer.steps" :key="step">{{ step }}</li>
            </ol>
          </div>
          <div v-if="answer.diagnosis.length" class="answer-section diagnosis-note">
            <h3><span>!</span>错因定位</h3>
            <p v-for="item in answer.diagnosis" :key="item">{{ item }}</p>
          </div>
          <div v-if="answer.workedExample" class="answer-section">
            <h3>
              <span>{{ sectionNumber('example') }}</span
              >例题或类比
            </h3>
            <p class="preserve-lines">{{ answer.workedExample }}</p>
          </div>
          <div v-if="answer.commonMistakes.length" class="answer-section caution-note">
            <h3>
              <span>{{ sectionNumber('mistakes') }}</span
              >容易出错
            </h3>
            <ul class="layer-list">
              <li v-for="item in answer.commonMistakes" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div v-if="answer.memoryTip" class="memory-note">
            <strong>记忆提示</strong>
            <p>{{ answer.memoryTip }}</p>
          </div>

          <section v-if="answer.keyClaims.length" class="evidence-ledger">
            <header><span>依据核对</span><small>展开可查看原始资料片段</small></header>
            <article v-for="claim in answer.keyClaims" :key="claim.text">
              <p>{{ claim.text }}</p>
              <span :class="`origin-${claim.origin.toLowerCase()}`">{{
                originLabel(claim.origin)
              }}</span>
              <details
                v-for="source in claim.sources"
                :key="`${claim.text}-${source.materialId}-${source.locator}`"
              >
                <summary>{{ source.fileName }} · {{ source.locator }}</summary>
                <blockquote>{{ source.snippet || '该资料片段未提供可展示摘要' }}</blockquote>
              </details>
            </article>
          </section>

          <section v-if="answer.evidenceConflicts.length" class="conflict-note">
            <strong>资料存在差异</strong>
            <p v-for="item in answer.evidenceConflicts" :key="item">{{ item }}</p>
          </section>
          <section v-if="answer.correctedPoints.length" class="correction-result">
            <header>本次修正</header>
            <div v-if="previousConclusion" class="correction-diff">
              <p><span>修正前</span>{{ previousConclusion }}</p>
              <p><span>修正后</span>{{ answer.conclusion }}</p>
            </div>
            <ul>
              <li v-for="item in answer.correctedPoints" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section v-if="answer.selfTestQuestion" class="self-test">
            <span class="section-number">{{ sectionNumber('selfTest') }} · 自我检查</span>
            <p>{{ answer.selfTestQuestion }}</p>
            <details v-if="answer.selfTestAnswer">
              <summary>完成后查看参考答案</summary>
              <p>{{ answer.selfTestAnswer }}</p>
            </details>
          </section>
        </template>

        <section class="final-conclusion">
          <template v-if="answer.mode !== 'SOLVE' || showFinalAnswer">
            <span>最终结论</span>
            <p>{{ answer.conclusion }}</p>
          </template>
          <el-button v-else type="warning" plain @click="showFinalAnswer = true"
            >查看最终答案</el-button
          >
        </section>

        <div v-if="showLearningBody && answer.limitations.length" class="limitations">
          <p v-for="item in answer.limitations" :key="item">说明：{{ item }}</p>
        </div>
        <div class="correction-box">
          <el-input v-model="correction" placeholder="指出疑问、资料冲突，或要求换一种讲法" />
          <el-button :loading="answering" @click="submitQuestion('CORRECT')">核对并修正</el-button>
        </div>
      </template>

      <div v-else class="lecture-empty">
        <p>LEARNING NOTE</p>
        <h2>一份能核对来源的学习讲义</h2>
        <ol>
          <li>先给结论和所需基础</li>
          <li>再按步骤解释，并指出易错点</li>
          <li>最后用资料来源和自测题收束</li>
        </ol>
      </div>
    </section>
  </div>
</template>
