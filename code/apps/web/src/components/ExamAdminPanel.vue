<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createAdminExam, deleteAdminExam, fetchAdminExams, updateAdminExam } from '../api/exam'
import { fetchAccounts } from '../api/management'
import type { ExamInput, ExamRecord } from '../types/exam'
import type { AccountSummary } from '../types/management'

const students = ref<AccountSummary[]>([])
const studentId = ref('')
const exams = ref<ExamRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogOpen = ref(false)
const editingId = ref('')
const form = reactive<ExamInput>({
  subject: '',
  examDate: '',
  startTime: '09:00:00',
  endTime: '11:00:00',
  location: '',
})

async function loadStudents(query = ''): Promise<void> {
  const page = await fetchAccounts(query, 0)
  students.value = page.items.filter((item) => item.role === 'STUDENT')
}

async function loadExams(): Promise<void> {
  if (!studentId.value) {
    exams.value = []
    return
  }
  loading.value = true
  try {
    exams.value = await fetchAdminExams(studentId.value)
  } catch {
    ElMessage.error('考试安排加载失败')
  } finally {
    loading.value = false
  }
}

function openForm(exam?: ExamRecord): void {
  editingId.value = exam?.id ?? ''
  Object.assign(
    form,
    exam
      ? {
          subject: exam.subject,
          examDate: exam.examDate,
          startTime: exam.startTime,
          endTime: exam.endTime,
          location: exam.location,
        }
      : { subject: '', examDate: '', startTime: '09:00:00', endTime: '11:00:00', location: '' },
  )
  dialogOpen.value = true
}

async function save(): Promise<void> {
  if (!studentId.value || !form.subject.trim() || !form.examDate || !form.location.trim()) {
    ElMessage.warning('请完整填写考试信息')
    return
  }
  if (form.endTime <= form.startTime) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return
  }
  saving.value = true
  try {
    const input = { ...form, subject: form.subject.trim(), location: form.location.trim() }
    if (editingId.value) await updateAdminExam(studentId.value, editingId.value, input)
    else await createAdminExam(studentId.value, input)
    dialogOpen.value = false
    await loadExams()
    ElMessage.success('考试安排已保存')
  } catch {
    ElMessage.error('考试安排保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(exam: ExamRecord): Promise<void> {
  try {
    await ElMessageBox.confirm(`删除“${exam.subject}”考试安排？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteAdminExam(studentId.value, exam.id)
    await loadExams()
    ElMessage.success('考试安排已删除')
  } catch {
    ElMessage.error('考试安排删除失败，请刷新后重试')
  }
}

onMounted(() => loadStudents())
</script>

<template>
  <section class="exam-admin-panel" v-loading="loading">
    <div class="exam-admin-toolbar">
      <el-select
        v-model="studentId"
        filterable
        remote
        :remote-method="loadStudents"
        placeholder="选择学生账号"
        @change="loadExams"
      >
        <el-option
          v-for="student in students"
          :key="student.id"
          :value="student.id"
          :label="`${student.nickname}（${student.username}）`"
        />
      </el-select>
      <el-button type="primary" :disabled="!studentId" @click="openForm()">新增考试安排</el-button>
    </div>
    <el-empty v-if="!studentId" description="请先选择学生" />
    <el-empty v-else-if="!exams.length && !loading" description="该学生暂无考试安排" />
    <el-table v-else :data="exams" row-key="id">
      <el-table-column prop="subject" label="考试科目" min-width="180" />
      <el-table-column prop="examDate" label="日期" width="130" />
      <el-table-column label="时间" width="170"
        ><template #default="scope"
          >{{ scope.row.startTime.slice(0, 5) }}—{{ scope.row.endTime.slice(0, 5) }}</template
        ></el-table-column
      >
      <el-table-column prop="location" label="地点" min-width="180" />
      <el-table-column label="操作" width="140"
        ><template #default="scope"
          ><el-button link type="primary" @click="openForm(scope.row)">编辑</el-button
          ><el-button link type="danger" @click="remove(scope.row)">删除</el-button></template
        ></el-table-column
      >
    </el-table>
    <el-dialog
      v-model="dialogOpen"
      :title="editingId ? '编辑考试安排' : '新增考试安排'"
      width="min(520px, 92vw)"
    >
      <el-form label-position="top">
        <el-form-item label="考试科目"
          ><el-input v-model="form.subject" maxlength="120"
        /></el-form-item>
        <el-form-item label="考试日期"
          ><el-date-picker v-model="form.examDate" type="date" value-format="YYYY-MM-DD"
        /></el-form-item>
        <div class="exam-time-row">
          <el-form-item label="开始时间"
            ><el-time-picker
              v-model="form.startTime"
              value-format="HH:mm:ss"
              format="HH:mm" /></el-form-item
          ><el-form-item label="结束时间"
            ><el-time-picker v-model="form.endTime" value-format="HH:mm:ss" format="HH:mm"
          /></el-form-item>
        </div>
        <el-form-item label="考试地点"
          ><el-input v-model="form.location" maxlength="200"
        /></el-form-item>
      </el-form>
      <template #footer
        ><el-button @click="dialogOpen = false">取消</el-button
        ><el-button type="primary" :loading="saving" @click="save">保存安排</el-button></template
      >
    </el-dialog>
  </section>
</template>

<style scoped>
.exam-admin-toolbar,
.exam-time-row {
  display: flex;
  gap: 16px;
}
.exam-admin-toolbar {
  margin-bottom: 24px;
}
.exam-admin-toolbar .el-select {
  width: min(420px, 60vw);
}
.exam-time-row > * {
  flex: 1;
}
@media (max-width: 700px) {
  .exam-admin-toolbar,
  .exam-time-row {
    flex-direction: column;
  }
  .exam-admin-toolbar .el-select {
    width: 100%;
  }
}
</style>
