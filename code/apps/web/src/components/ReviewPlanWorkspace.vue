<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import '../review-plan.css'

import {
  createReviewPlan,
  deleteReviewPlan,
  fetchReviewPlans,
  regenerateReviewPlan,
} from '../api/learning'
import type { ExamRecord } from '../types/exam'
import type { MeData } from '../types/identity'
import type { ReviewPlan } from '../types/learning'

const props = defineProps<{ exams: ExamRecord[]; me: MeData }>()

const form = reactive({ examIds: [] as string[], dailyMinutes: 120, target: '', constraints: '' })
const plans = ref<ReviewPlan[]>([])
const selectedId = ref('')
const loading = ref(false)
const generating = ref(false)
const activePlan = computed(
  () => plans.value.find((item) => item.id === selectedId.value) ?? plans.value[0],
)
const upcoming = computed(() =>
  props.exams.filter(
    (exam) => new Date(`${exam.examDate}T${exam.endTime}`).getTime() >= Date.now(),
  ),
)
const canPlan = computed(() => props.me.authorizations.EXAMS.granted)
const phaseName: Record<string, string> = {
  FOUNDATION: '基础回顾',
  PRACTICE: '强化训练',
  SPRINT: '考前冲刺',
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric' }).format(
    new Date(`${value}T00:00:00`),
  )
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadPlans(): Promise<void> {
  if (!canPlan.value) return
  loading.value = true
  try {
    plans.value = await fetchReviewPlans()
    if (!plans.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = plans.value.find((item) => item.isCurrent)?.id ?? plans.value[0]?.id ?? ''
    }
  } catch {
    ElMessage.error('复习计划加载失败，请检查 Agent 服务')
  } finally {
    loading.value = false
  }
}

async function generate(): Promise<void> {
  if (!form.examIds.length) return void ElMessage.warning('请至少选择一场考试')
  if (!form.target.trim()) return void ElMessage.warning('请填写本次复习目标')
  generating.value = true
  try {
    const result = await createReviewPlan({
      ...form,
      target: form.target.trim(),
      constraints: form.constraints.trim(),
    })
    await loadPlans()
    selectedId.value = result.id
    ElMessage.success('复习计划已生成并保存')
  } catch {
    ElMessage.error('计划生成失败，请检查考试授权、模型配置或稍后重试')
  } finally {
    generating.value = false
  }
}

async function regenerate(plan: ReviewPlan): Promise<void> {
  generating.value = true
  try {
    const result = await regenerateReviewPlan(plan.id)
    await loadPlans()
    selectedId.value = result.id
    ElMessage.success(`已保存为第 ${result.versionNumber} 版，旧版仍可查看`)
  } catch {
    ElMessage.error('重新生成失败，原计划未受影响')
  } finally {
    generating.value = false
  }
}

async function remove(plan: ReviewPlan): Promise<void> {
  try {
    await ElMessageBox.confirm('将删除该计划的全部历史版本，是否继续？', '删除复习计划', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteReviewPlan(plan.id)
    await loadPlans()
    ElMessage.success('复习计划已删除')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error('复习计划删除失败')
  }
}

onMounted(loadPlans)
</script>

<template>
  <section class="review-workspace">
    <div v-if="!canPlan" class="review-permission">
      <strong>需要考试数据授权</strong>
      <p>请在个人中心开启“考试与学习计划”，再根据你的考试安排生成计划。</p>
    </div>

    <template v-else>
      <section class="route-builder">
        <header>
          <div>
            <p class="panel-label">REVIEW ROUTE · 复习航线</p>
            <h2>先确定时间边界，再安排每一段学习。</h2>
          </div>
          <span>日期与总时长由系统核算</span>
        </header>
        <el-checkbox-group v-model="form.examIds" class="exam-ticket-list">
          <el-checkbox v-for="exam in upcoming" :key="exam.id" :value="exam.id" border>
            <strong>{{ exam.subject }}</strong>
            <small>{{ formatDate(exam.examDate) }} · {{ exam.location }}</small>
          </el-checkbox>
        </el-checkbox-group>
        <el-empty v-if="!upcoming.length" description="暂无可用的待考安排" :image-size="70" />
        <div class="route-form">
          <label>
            <span>每日可用时间</span>
            <el-input-number v-model="form.dailyMinutes" :min="15" :max="720" :step="15" />
            <small>分钟</small>
          </label>
          <label>
            <span>复习目标</span>
            <el-input
              v-model="form.target"
              maxlength="300"
              placeholder="例如：掌握核心题型，稳定达到 80 分"
            />
          </label>
          <label>
            <span>学习偏好与限制</span>
            <el-input
              v-model="form.constraints"
              maxlength="1000"
              placeholder="例如：周三只做轻量背诵，不安排综合题"
            />
            <small>用于调整学习方法，不改变上方设定的每日总时长</small>
          </label>
          <el-button
            type="primary"
            :loading="generating"
            :disabled="!upcoming.length"
            @click="generate"
          >
            生成并保存计划
          </el-button>
        </div>
      </section>

      <section v-loading="loading" class="plan-ledger">
        <aside v-if="plans.length" class="plan-versions" aria-label="复习计划版本">
          <button
            v-for="plan in plans"
            :key="plan.id"
            :class="{ active: activePlan?.id === plan.id }"
            @click="selectedId = plan.id"
          >
            <span>v{{ plan.versionNumber }} <em v-if="plan.isCurrent">当前</em></span>
            <strong>{{ plan.title }}</strong>
            <small>{{ formatDateTime(plan.createdAt) }}</small>
          </button>
        </aside>

        <article v-if="activePlan" class="plan-sheet">
          <header class="plan-sheet-heading">
            <div>
              <p class="panel-label">计划版本 v{{ activePlan.versionNumber }}</p>
              <h2>{{ activePlan.title }}</h2>
              <p>{{ activePlan.target }}</p>
            </div>
            <div class="plan-actions">
              <span v-if="activePlan.stale" class="stale-badge">考试信息已变更</span>
              <el-button :loading="generating" @click="regenerate(activePlan)"
                >按最新数据重新生成</el-button
              >
              <el-button type="danger" plain @click="remove(activePlan)">删除全部版本</el-button>
            </div>
          </header>

          <div class="plan-facts">
            <div>
              <small>计划总时长</small><strong>{{ activePlan.totalMinutes }} 分钟</strong>
            </div>
            <div>
              <small>数据截至</small><strong>{{ formatDateTime(activePlan.dataAsOf) }}</strong>
            </div>
            <div>
              <small>生成模型</small><strong>{{ activePlan.modelName || '未记录' }}</strong>
            </div>
          </div>

          <p class="priority-note"><strong>排序依据</strong>{{ activePlan.priorityExplanation }}</p>
          <div class="review-route" aria-label="复习阶段路线">
            <article
              v-for="stage in activePlan.stages"
              :key="stage.id"
              :class="`phase-${stage.phase.toLowerCase()}`"
            >
              <div class="route-node">
                <span>{{ stage.stageIndex + 1 }}</span>
              </div>
              <div class="route-stage">
                <header>
                  <span>{{ phaseName[stage.phase] }} · {{ stage.subject }}</span>
                  <strong>{{ stage.suggestedMinutes }} 分钟</strong>
                </header>
                <h3>{{ stage.objective }}</h3>
                <p>{{ stage.method }}</p>
                <small>{{ formatDate(stage.startDate) }}—{{ formatDate(stage.endDate) }}</small>
                <div v-if="stage.knowledgePoints.length" class="knowledge-tags">
                  <span v-for="point in stage.knowledgePoints" :key="point">{{ point }}</span>
                </div>
                <blockquote>{{ stage.rationale }}</blockquote>
              </div>
            </article>
          </div>

          <details class="plan-basis">
            <summary>查看假设、限制与输入快照</summary>
            <p><strong>学习偏好与限制：</strong>{{ activePlan.constraints || '未填写' }}</p>
            <p v-for="item in activePlan.assumptions" :key="item">假设：{{ item }}</p>
            <p v-for="item in activePlan.limitations" :key="item">限制：{{ item }}</p>
          </details>
        </article>

        <el-empty v-else description="选择考试并生成第一份复习计划" />
      </section>
    </template>
  </section>
</template>
