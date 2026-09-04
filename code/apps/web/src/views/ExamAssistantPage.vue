<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createExam, deleteExam, fetchExams, updateExam } from '../api/exam'
import ExamLearningWorkspace from '../components/ExamLearningWorkspace.vue'
import type { ExamInput, ExamRecord } from '../types/exam'
import type { MeData, UserSummary } from '../types/identity'

defineProps<{ user: UserSummary; me: MeData }>()

const exams = ref<ExamRecord[]>([])
const activeView = ref<'schedule' | 'learning'>('schedule')
const loading = ref(false)
const saving = ref(false)
const dialogOpen = ref(false)
const editingId = ref('')
const now = ref(new Date())
const form = reactive<ExamInput>({
  subject: '',
  examDate: '',
  startTime: '09:00:00',
  endTime: '11:00:00',
  location: '',
})

const upcomingExams = computed(() =>
  exams.value.filter((exam) => examEnd(exam).getTime() >= now.value.getTime()),
)
const historyExams = computed(() =>
  exams.value.filter((exam) => examEnd(exam).getTime() < now.value.getTime()).reverse(),
)
const nextExam = computed(() => upcomingExams.value[0] ?? null)

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

function resetForm(): void {
  editingId.value = ''
  Object.assign(form, {
    subject: '',
    examDate: '',
    startTime: '09:00:00',
    endTime: '11:00:00',
    location: '',
  })
}

function openCreate(): void {
  resetForm()
  dialogOpen.value = true
}

function openEdit(exam: ExamRecord): void {
  editingId.value = exam.id
  Object.assign(form, {
    subject: exam.subject,
    examDate: exam.examDate,
    startTime: exam.startTime,
    endTime: exam.endTime,
    location: exam.location,
  })
  dialogOpen.value = true
}

function validForm(): boolean {
  if (!form.subject.trim() || !form.examDate || !form.location.trim()) {
    ElMessage.warning('请填写科目、日期和地点')
    return false
  }
  if (!form.startTime || !form.endTime || form.endTime <= form.startTime) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return false
  }
  return true
}

async function reload(): Promise<void> {
  exams.value = await fetchExams()
  now.value = new Date()
}

async function save(): Promise<void> {
  if (!validForm()) return
  saving.value = true
  try {
    const input = { ...form, subject: form.subject.trim(), location: form.location.trim() }
    if (editingId.value) await updateExam(editingId.value, input)
    else await createExam(input)
    await reload()
    dialogOpen.value = false
    ElMessage.success(editingId.value ? '考试安排已更新' : '考试安排已添加')
  } catch {
    ElMessage.error('保存失败，请检查时间后重试')
  } finally {
    saving.value = false
  }
}

async function remove(exam: ExamRecord): Promise<void> {
  try {
    await ElMessageBox.confirm(`删除“${exam.subject}”的考试安排？`, '删除考试', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteExam(exam.id)
    await reload()
    ElMessage.success('考试安排已删除')
  } catch {
    ElMessage.error('删除失败，请刷新后重试')
  }
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
        <p class="page-kicker">Exam assistant · 考试与规划</p>
        <h1 id="exam-title">先把时间放上桌面，再安排如何走到终点。</h1>
        <p>考试记录不依赖 AI；只有你主动发起时，助手才会读取授权数据。</p>
      </div>
      <button class="exam-add-seal" type="button" @click="openCreate">
        <span>+</span><strong>添加考试</strong>
      </button>
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
            <span>后开始</span>
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
            <p>考试时间轴还是空的</p>
            <h2>记下第一场考试</h2>
            <span>添加后会自动排序，并在这里显示最近一场。</span>
          </div>
        </article>

        <aside class="exam-plan-entry">
          <p class="panel-label">AI 学习助手</p>
          <h2>从一道不会的题开始</h2>
          <p>讲解、解析、错因诊断、个性化练习和阶段计划将在同一段对话中衔接。</p>
          <el-button type="primary" @click="activeView = 'learning'">进入 AI 学习工作台</el-button>
        </aside>
      </section>

      <section class="exam-timeline-panel">
        <header>
          <div>
            <p class="panel-label">考试时间轴</p>
            <h2>接下来的安排</h2>
          </div>
          <span>{{ upcomingExams.length }} 场待考</span>
        </header>

        <el-empty v-if="!upcomingExams.length && !loading" description="暂无待考记录">
          <el-button type="primary" @click="openCreate">添加考试</el-button>
        </el-empty>
        <div v-else class="exam-timeline">
          <article v-for="(exam, index) in upcomingExams" :key="exam.id">
            <div class="timeline-marker">
              <span>{{ index + 1 }}</span>
            </div>
            <div class="timeline-date">
              <strong>{{ displayDate(exam.examDate) }}</strong>
              <span>{{ displayTime(exam.startTime) }}—{{ displayTime(exam.endTime) }}</span>
            </div>
            <div class="timeline-subject">
              <h3>{{ exam.subject }}</h3>
              <p>{{ exam.location }}</p>
            </div>
            <div class="timeline-actions">
              <button type="button" @click="openEdit(exam)">编辑</button>
              <button type="button" class="danger" @click="remove(exam)">删除</button>
            </div>
          </article>
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
            <button type="button" @click="remove(exam)">删除</button>
          </article>
        </div>
      </details>
    </template>

    <ExamLearningWorkspace v-else :exams="upcomingExams" :me="me" />

    <el-dialog
      v-model="dialogOpen"
      :title="editingId ? '编辑考试' : '添加考试'"
      width="min(520px, 92vw)"
      @closed="resetForm"
    >
      <el-form label-position="top" class="exam-form">
        <el-form-item label="考试科目" required>
          <el-input v-model="form.subject" maxlength="120" placeholder="例如：数据结构" />
        </el-form-item>
        <el-form-item label="考试日期" required>
          <el-date-picker
            v-model="form.examDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
          />
        </el-form-item>
        <div class="exam-time-fields">
          <el-form-item label="开始时间" required
            ><el-time-picker v-model="form.startTime" value-format="HH:mm:ss" format="HH:mm"
          /></el-form-item>
          <el-form-item label="结束时间" required
            ><el-time-picker v-model="form.endTime" value-format="HH:mm:ss" format="HH:mm"
          /></el-form-item>
        </div>
        <el-form-item label="考试地点" required>
          <el-input v-model="form.location" maxlength="200" placeholder="例如：教学楼 A201" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存安排</el-button>
      </template>
    </el-dialog>
  </section>
</template>
