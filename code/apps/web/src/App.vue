<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { logout, restoreSession } from './api/auth'
import AuthGateway from './components/AuthGateway.vue'
import {
  cleanupData,
  fetchAuditEvents,
  fetchMe,
  savePreference,
  saveProfile,
  setAuthorization,
} from './api/user'
import type { AuditEvent, DataScope, MeData, UserSummary } from './types/identity'

const scopeLabels: Record<DataScope, { title: string; description: string }> = {
  EXAMS: { title: '考试数据', description: '用于生成与考试时间匹配的学习计划' },
  MASTERY: { title: '掌握情况', description: '用于识别薄弱知识点和复习优先级' },
  DIET: { title: '饮食与过敏信息', description: '用于过滤忌口、过敏原和饮食目标' },
  CHAT_HISTORY: { title: '历史会话', description: '用于在新任务中参考长期对话摘要' },
}

const currentUser = ref<UserSummary | null>(null)
const me = ref<MeData | null>(null)
const auditEvents = ref<AuditEvent[]>([])
const activeTab = ref('profile')
const profileForm = reactive({ nickname: '', avatarUrl: '', contact: '' })
const preferenceForm = reactive({
  tastes: [] as string[],
  budget: null as number | null,
  avoidances: [] as string[],
  allergens: [] as string[],
  dietaryGoal: '',
})
const isStudent = computed(() => currentUser.value?.role === 'STUDENT')

async function loadMe(): Promise<void> {
  const data = await fetchMe()
  me.value = data
  Object.assign(profileForm, {
    nickname: data.profile.nickname,
    avatarUrl: data.profile.avatarUrl ?? '',
    contact: data.profile.contact ?? '',
  })
  Object.assign(preferenceForm, {
    tastes: [...data.preference.tastes],
    budget: data.preference.budget,
    avoidances: [...data.preference.avoidances],
    allergens: [...data.preference.allergens],
    dietaryGoal: data.preference.dietaryGoal ?? '',
  })
}

async function handleAuthenticated(user: UserSummary): Promise<void> {
  currentUser.value = user
  await loadMe()
}

async function submitLogout(): Promise<void> {
  await logout()
  currentUser.value = null
  me.value = null
  auditEvents.value = []
  ElMessage.success('已安全退出')
}

async function submitProfile(): Promise<void> {
  const profile = await saveProfile(profileForm)
  if (me.value) me.value.profile = profile
  if (currentUser.value) currentUser.value.nickname = profile.nickname
  ElMessage.success('个人资料已保存')
}

async function submitPreference(): Promise<void> {
  const preference = await savePreference(preferenceForm)
  if (me.value) me.value.preference = preference
  ElMessage.success('饮食偏好已保存')
}

async function toggleAuthorization(scope: DataScope, granted: boolean): Promise<void> {
  if (!me.value) return
  if (!granted)
    await ElMessageBox.confirm(
      `撤回“${scopeLabels[scope].title}”授权后，新分析将立即停止使用该数据，并清理对应长期记忆。`,
      '确认撤回授权',
      { type: 'warning', confirmButtonText: '确认撤回', cancelButtonText: '取消' },
    )
  try {
    me.value.authorizations[scope] = await setAuthorization(scope, granted)
    ElMessage.success(granted ? '授权已生效' : '授权已撤回并完成清理')
  } catch (error) {
    me.value.authorizations[scope].granted = !granted
    throw error
  }
}

async function submitCleanup(): Promise<void> {
  await ElMessageBox.confirm('将清理全部四类长期记忆，审计记录依法保留。', '清理个人数据', {
    type: 'warning',
    confirmButtonText: '确认清理',
    cancelButtonText: '取消',
  })
  await cleanupData(Object.keys(scopeLabels) as DataScope[])
  ElMessage.success('长期记忆清理完成')
}

async function loadAudits(): Promise<void> {
  auditEvents.value = (await fetchAuditEvents()).items
}

function openAudit(): void {
  activeTab.value = 'audit'
  void loadAudits()
}

function handleAuthorizationChange(scope: DataScope, value: string | number | boolean): void {
  void toggleAuthorization(scope, value === true)
}

onMounted(async () => {
  const tokens = await restoreSession()
  if (tokens) {
    currentUser.value = tokens.user
    await loadMe()
  }
})
</script>

<template>
  <AuthGateway v-if="!currentUser" @authenticated="handleAuthenticated" />

  <main v-else class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">智慧校园智能体</p>
        <strong>{{ currentUser.nickname }}</strong
        ><el-tag size="small">{{ isStudent ? '学生' : '信息资料管理员' }}</el-tag>
      </div>
      <el-button @click="submitLogout">安全退出</el-button>
    </header>
    <section class="workspace">
      <aside class="sidebar">
        <button :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">
          个人资料
        </button>
        <button
          v-if="isStudent"
          :class="{ active: activeTab === 'preference' }"
          @click="activeTab = 'preference'"
        >
          饮食偏好
        </button>
        <button
          v-if="isStudent"
          :class="{ active: activeTab === 'authorization' }"
          @click="activeTab = 'authorization'"
        >
          数据授权
        </button>
        <button :class="{ active: activeTab === 'audit' }" @click="openAudit">安全记录</button>
      </aside>
      <section v-if="me" class="content-card">
        <template v-if="activeTab === 'profile'">
          <p class="eyebrow">个人中心</p>
          <h2>非核心资料</h2>
          <dl v-if="isStudent" class="identity-facts">
            <div>
              <dt>学号</dt>
              <dd>{{ me.profile.studentNumber }}</dd>
            </div>
            <div>
              <dt>姓名</dt>
              <dd>{{ me.profile.realName }}</dd>
            </div>
            <div>
              <dt>手机号</dt>
              <dd>{{ me.profile.phone }}</dd>
            </div>
          </dl>
          <el-form v-if="isStudent" label-position="top" @submit.prevent="submitProfile">
            <el-form-item label="昵称"
              ><el-input v-model="profileForm.nickname" maxlength="80"
            /></el-form-item>
            <el-form-item label="头像地址"
              ><el-input v-model="profileForm.avatarUrl" maxlength="500"
            /></el-form-item>
            <el-form-item label="联系方式"
              ><el-input v-model="profileForm.contact" maxlength="120"
            /></el-form-item>
            <el-button native-type="submit" type="primary">保存资料</el-button>
          </el-form>
          <el-descriptions v-else :column="1" border
            ><el-descriptions-item label="账号">{{ me.profile.username }}</el-descriptions-item
            ><el-descriptions-item label="昵称">{{ me.profile.nickname }}</el-descriptions-item
            ><el-descriptions-item label="角色"
              >信息资料管理员</el-descriptions-item
            ></el-descriptions
          >
        </template>
        <template v-else-if="activeTab === 'preference'">
          <p class="eyebrow">个人中心</p>
          <h2>饮食偏好</h2>
          <el-form label-position="top" @submit.prevent="submitPreference">
            <el-form-item label="口味"
              ><el-select v-model="preferenceForm.tastes" multiple allow-create filterable
            /></el-form-item>
            <el-form-item label="单餐预算"
              ><el-input-number v-model="preferenceForm.budget" :min="0" :precision="2"
            /></el-form-item>
            <el-form-item label="忌口"
              ><el-select v-model="preferenceForm.avoidances" multiple allow-create filterable
            /></el-form-item>
            <el-form-item label="过敏原"
              ><el-select v-model="preferenceForm.allergens" multiple allow-create filterable
            /></el-form-item>
            <el-form-item label="饮食目标"
              ><el-input v-model="preferenceForm.dietaryGoal" maxlength="200"
            /></el-form-item>
            <el-button native-type="submit" type="primary">保存偏好</el-button>
          </el-form>
        </template>
        <template v-else-if="activeTab === 'authorization'">
          <p class="eyebrow">隐私控制</p>
          <h2>AI 数据授权</h2>
          <p class="muted">四类数据默认不授权。每项授权可以独立开启或撤回。</p>
          <div class="authorization-list">
            <div v-for="(label, scope) in scopeLabels" :key="scope" class="authorization-item">
              <div>
                <strong>{{ label.title }}</strong>
                <p>{{ label.description }}</p>
              </div>
              <el-switch
                v-model="me.authorizations[scope].granted"
                :aria-label="label.title"
                @change="handleAuthorizationChange(scope, $event)"
              />
            </div>
          </div>
          <el-button type="danger" plain @click="submitCleanup">清理全部长期记忆</el-button>
        </template>
        <template v-else>
          <p class="eyebrow">审计与安全</p>
          <h2>最近安全记录</h2>
          <el-empty v-if="auditEvents.length === 0" description="暂无记录" />
          <el-table v-else :data="auditEvents" stripe
            ><el-table-column prop="eventType" label="事件" min-width="170" /><el-table-column
              prop="outcome"
              label="结果"
              width="100" /><el-table-column prop="occurredAt" label="时间" min-width="210"
          /></el-table>
        </template>
      </section>
    </section>
  </main>
</template>
