<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchExams } from '../api/exam'
import ExamLearningWorkspace from '../components/ExamLearningWorkspace.vue'
import type { ExamRecord } from '../types/exam'
import type { MeData, UserSummary } from '../types/identity'

defineProps<{ user: UserSummary; me: MeData }>()

const exams = ref<ExamRecord[]>([])
const activeView = ref<'schedule' | 'learning'>('schedule')
const loading = ref(false)
const now = ref(new Date())
const refreshedAt = ref<Date | null>(null)

const upcomingExams = computed(() =>
  exams.value
    .filter((exam) => examEnd(exam).getTime() >= now.value.getTime())
    .sort((left, right) => examStart(left).getTime() - examStart(right).getTime()),
)
const historyExams = computed(() =>
  exams.value.filter((exam) => examEnd(exam).getTime() < now.value.getTime()).reverse(),
)
const nextExam = computed(() => upcomingExams.value[0] ?? null)
const nextExamInProgress = computed(
  () =>
    nextExam.value !== null &&
    examStart(nextExam.value).getTime() <= now.value.getTime() &&
    examEnd(nextExam.value).getTime() >= now.value.getTime(),
)
const examGroups = computed(() => {
  const groups = [
    { key: 'urgent', label: '7 天内', note: '优先复习', exams: [] as ExamRecord[] },
    { key: 'month', label: '30 天内', note: '纳入计划', exams: [] as ExamRecord[] },
    { key: 'later', label: '稍后', note: '提前了解', exams: [] as ExamRecord[] },
  ]
  upcomingExams.value.forEach((exam) => {
    const days = Math.max(
      0,
      Math.ceil((examStart(exam).getTime() - now.value.getTime()) / 86_400_000),
    )
    groups[days <= 7 ? 0 : days <= 30 ? 1 : 2].exams.push(exam)
  })
  return groups.filter((group) => group.exams.length)
})

function examStart(exam: ExamRecord): Date {
  return new Date(`${exam.examDate}T${exam.startTime}`)
}

function examEnd(exam: ExamRecord): Date {
  return new Date(`${exam.examDate}T${exam.endTime}`)
}

function countdown(exam: ExamRecord): string {
  const milliseconds = examStart(exam).getTime() - now.value.getTime()
  if (milliseconds <= 0) return '正在进行'
  const minutes = Math.ceil(milliseconds / 60_000)
  const days = Math.floor(minutes / 1440)
  const hours = Math.floor((minutes % 1440) / 60)
  if (days > 0) return `${days} 天 ${hours} 小时`
  if (hours > 0) return `${hours} 小时 ${minutes % 60} 分`
  return `${minutes} 分钟`
}

function displayDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  }).format(new Date(`${value}T00:00:00`))
}

function displayTime(value: string): string {
  return value.slice(0, 5)
}

function wasUpdated(exam: ExamRecord): boolean {
  return new Date(exam.updatedAt).getTime() - new Date(exam.createdAt).getTime() > 1000
}

async function reload(): Promise<void> {
  exams.value = await fetchExams()
  now.value = new Date()
  refreshedAt.value = new Date()
}

onMounted(async () => {
  loading.value = true
  try {
    await reload()
  } catch {
    ElMessage.error('考试安排加载失败，请确认服务正在运行')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="module-page module-exam exam-assistant" aria-labelledby="exam-title">
    <header class="module-hero exam-hero">
      <div>
        <p class="page-kicker">Exam assistant · 考试助手</p>
        <h1 id="exam-title">考试信息一目了然，把注意力留给学习本身。</h1>
        <p>考试安排由管理员统一维护；AI 学习助手仅在你主动发起时工作。</p>
      </div>
    </header>

    <nav class="module-tabs exam-main-tabs" aria-label="考试助手功能">
      <button :class="{ active: activeView === 'schedule' }" @click="activeView = 'schedule'">
        考试安排
      </button>
      <button :class="{ active: activeView === 'learning' }" @click="activeView = 'learning'">
        AI 学习工作台
      </button>
    </nav>

    <template v-if="activeView === 'schedule'">
      <section v-loading="loading" class="exam-schedule-grid">
        <article v-if="nextExam" class="next-exam-focus">
          <div class="exam-focus-date">
            <small>NEXT EXAM</small>
            <strong>{{ countdown(nextExam) }}</strong>
            <span v-if="!nextExamInProgress">后开始</span>
          </div>
          <div class="exam-focus-copy">
            <p>{{ displayDate(nextExam.examDate) }}</p>
            <h2>{{ nextExam.subject }}</h2>
            <dl>
              <div>
                <dt>时间</dt>
                <dd>{{ displayTime(nextExam.startTime) }}—{{ displayTime(nextExam.endTime) }}</dd>
              </div>
              <div>
                <dt>地点</dt>
                <dd>{{ nextExam.location }}</dd>
              </div>
            </dl>
          </div>
        </article>

        <article v-else class="next-exam-focus exam-empty-focus">
          <div class="exam-focus-date"><small>NEXT EXAM</small><strong>—</strong></div>
          <div class="exam-focus-copy">
            <p>尚未发布考试安排</p>
            <h2>暂无考试信息</h2>
            <span>管理员发布后会自动排序，并在这里显示最近一场。</span>
          </div>
        </article>

        <aside class="exam-learning-entry">
          <p class="panel-label">AI 学习助手</p>
          <h2>从一道不会的题开始</h2>
          <p>讲解、解析、错因诊断、个性化练习和错题复盘在同一个工作台中衔接。</p>
          <el-button type="primary" @click="activeView = 'learning'">进入 AI 学习工作台</el-button>
        </aside>
      </section>

      <section class="exam-timeline-panel">
        <header>
          <div>
            <p class="panel-label">考试时间轴</p>
            <h2>接下来的安排</h2>
          </div>
          <span>
            {{ upcomingExams.length }} 场待考
            <small v-if="refreshedAt">· {{ displayTime(refreshedAt.toTimeString()) }} 已同步</small>
          </span>
        </header>

        <el-empty v-if="!upcomingExams.length && !loading" description="管理员尚未发布待考安排" />
        <div v-else class="exam-timeline exam-grouped-timeline">
          <section v-for="group in examGroups" :key="group.key" class="exam-time-group">
            <header>
              <strong>{{ group.label }}</strong>
              <span>{{ group.note }}</span>
            </header>
            <article v-for="(exam, index) in group.exams" :key="exam.id">
              <div class="timeline-marker">
                <span>{{ index + 1 }}</span>
              </div>
              <div class="timeline-date">
                <strong>{{ displayDate(exam.examDate) }}</strong>
                <span>{{ displayTime(exam.startTime) }}—{{ displayTime(exam.endTime) }}</span>
              </div>
              <div class="timeline-subject">
                <h3>{{ exam.subject }} <em v-if="wasUpdated(exam)">已更新</em></h3>
                <p>{{ exam.location }}</p>
              </div>
            </article>
          </section>
        </div>
      </section>

      <details v-if="historyExams.length" class="exam-history">
        <summary>
          历史考试 <span>{{ historyExams.length }}</span>
        </summary>
        <div>
          <article v-for="exam in historyExams" :key="exam.id">
            <span>{{ exam.examDate }}</span
            ><strong>{{ exam.subject }}</strong
            ><small>{{ exam.location }}</small>
          </article>
        </div>
      </details>
    </template>

    <ExamLearningWorkspace v-else :me="me" :exams="exams" />
  </section>
</template>

<style scoped>
.exam-timeline-panel > header > span small {
  color: #849198;
  font-weight: 400;
}
.exam-grouped-timeline {
  display: grid;
  gap: 25px;
}
.exam-time-group > header {
  display: flex;
  gap: 10px;
  align-items: baseline;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e3ded2;
}
.exam-time-group > header strong {
  color: #2f454e;
  font:
    600 19px Georgia,
    'Microsoft YaHei',
    serif;
}
.exam-time-group > header span {
  color: #8a7750;
  font-size: 12px;
}
.timeline-subject em {
  margin-left: 7px;
  padding: 3px 6px;
  border-radius: 3px;
  color: #fff;
  background: #0d756d;
  font-size: 10px;
  font-style: normal;
  vertical-align: middle;
}
</style>
