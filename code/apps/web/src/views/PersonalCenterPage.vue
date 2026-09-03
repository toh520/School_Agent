<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  cleanupData,
  fetchAuditEvents,
  savePreference,
  saveProfile,
  setAuthorization,
} from '../api/user'
import type { AuditEvent, DataScope, MeData, Profile, UserSummary } from '../types/identity'

const props = defineProps<{ user: UserSummary; me: MeData }>()
const emit = defineEmits<{ 'profile-updated': [profile: Profile] }>()

const activeSection = ref<'identity' | 'safety' | 'authorization' | 'audit'>('identity')
const auditEvents = ref<AuditEvent[]>([])
const auditLoaded = ref(false)
const profileForm = reactive({ nickname: '', avatarUrl: '', contact: '' })
const safetyForm = reactive({ avoidances: [] as string[], allergens: [] as string[] })

const scopeLabels: Record<DataScope, { title: string; description: string }> = {
  EXAMS: { title: '考试数据', description: '用于读取本人考试安排并生成复习计划' },
  MASTERY: { title: '掌握情况', description: '用于识别薄弱知识点和复习优先级' },
  DIET: { title: '饮食安全档案', description: '用于过滤过敏原和长期明确忌口' },
  CHAT_HISTORY: { title: '历史会话', description: '用于在新任务中参考长期对话摘要' },
}

watch(
  () => props.me,
  (data) => {
    Object.assign(profileForm, {
      nickname: data.profile.nickname,
      avatarUrl: data.profile.avatarUrl ?? '',
      contact: data.profile.contact ?? '',
    })
    Object.assign(safetyForm, {
      avoidances: [...data.preference.avoidances],
      allergens: [...data.preference.allergens],
    })
  },
  { immediate: true },
)

async function submitProfile(): Promise<void> {
  const profile = await saveProfile(profileForm)
  emit('profile-updated', profile)
  ElMessage.success('个人资料已保存')
}

async function submitSafetyProfile(): Promise<void> {
  const preference = await savePreference({
    // Transitional fields are preserved until the food-domain migration removes them safely.
    tastes: props.me.preference.tastes,
    budget: props.me.preference.budget,
    dietaryGoal: props.me.preference.dietaryGoal ?? '',
    avoidances: safetyForm.avoidances,
    allergens: safetyForm.allergens,
  })
  props.me.preference = preference
  ElMessage.success('饮食安全档案已保存')
}

async function toggleAuthorization(scope: DataScope, granted: boolean): Promise<void> {
  if (!granted) {
    await ElMessageBox.confirm(
      `撤回“${scopeLabels[scope].title}”授权后，新任务将立即停止使用该数据，并清理对应长期记忆。`,
      '确认撤回授权',
      { type: 'warning', confirmButtonText: '确认撤回', cancelButtonText: '取消' },
    )
  }
  try {
    props.me.authorizations[scope] = await setAuthorization(scope, granted)
    ElMessage.success(granted ? '授权已生效' : '授权已撤回并完成清理')
  } catch (error) {
    props.me.authorizations[scope].granted = !granted
    throw error
  }
}

function handleAuthorizationChange(scope: DataScope, value: string | number | boolean): void {
  void toggleAuthorization(scope, value === true)
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

async function openAudit(): Promise<void> {
  activeSection.value = 'audit'
  if (auditLoaded.value) return
  auditEvents.value = (await fetchAuditEvents()).items
  auditLoaded.value = true
}
</script>

<template>
  <section class="profile-page" aria-labelledby="profile-title">
    <header class="profile-heading">
      <div>
        <p class="page-kicker">Student profile · 本人档案</p>
        <h1 id="profile-title">个人中心</h1>
        <p>只在这里维护长期稳定的信息；每次任务的临时条件留在对应模块中。</p>
      </div>
      <div class="profile-heading-avatar">
        <img v-if="me.profile.avatarUrl" :src="me.profile.avatarUrl" alt="个人头像" />
        <span v-else>{{ user.nickname.slice(0, 1) }}</span>
      </div>
    </header>

    <div class="profile-workspace">
      <nav class="profile-sections" aria-label="个人中心分区">
        <button
          :class="{ active: activeSection === 'identity' }"
          @click="activeSection = 'identity'"
        >
          <span>身份</span>基本资料
        </button>
        <button :class="{ active: activeSection === 'safety' }" @click="activeSection = 'safety'">
          <span>饮食</span>安全档案
        </button>
        <button
          :class="{ active: activeSection === 'authorization' }"
          @click="activeSection = 'authorization'"
        >
          <span>隐私</span>数据授权
        </button>
        <button :class="{ active: activeSection === 'audit' }" @click="openAudit">
          <span>审计</span>安全记录
        </button>
      </nav>

      <section v-if="activeSection === 'identity'" class="profile-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-label">Identity</p>
            <h2>身份与联系方式</h2>
          </div>
          <span class="status-pill">核心身份只读</span>
        </div>
        <dl class="identity-ledger">
          <div>
            <dt>姓名</dt>
            <dd>{{ me.profile.realName }}</dd>
          </div>
          <div>
            <dt>学号</dt>
            <dd>{{ me.profile.studentNumber }}</dd>
          </div>
          <div>
            <dt>登录账号</dt>
            <dd>{{ me.profile.username }}</dd>
          </div>
          <div>
            <dt>手机号</dt>
            <dd>{{ me.profile.phone }}</dd>
          </div>
        </dl>
        <el-form label-position="top" class="profile-form" @submit.prevent="submitProfile">
          <div class="profile-form-grid">
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" maxlength="80" show-word-limit />
            </el-form-item>
            <el-form-item label="联系方式">
              <el-input
                v-model="profileForm.contact"
                maxlength="120"
                placeholder="邮箱或其他联系方式"
              />
            </el-form-item>
            <el-form-item class="full-field" label="头像地址">
              <el-input v-model="profileForm.avatarUrl" maxlength="500" placeholder="https://…" />
            </el-form-item>
          </div>
          <el-button native-type="submit" type="primary">保存个人资料</el-button>
        </el-form>
      </section>

      <section v-else-if="activeSection === 'safety'" class="profile-panel safety-profile-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-label">Dining safety</p>
            <h2>长期饮食安全档案</h2>
          </div>
          <span class="status-pill status-danger">推荐硬约束</span>
        </div>
        <p class="panel-description">
          这里只保存长期有效的过敏原和明确忌口。口味、预算和本次目标将在每次请求推荐时填写。
        </p>
        <el-form label-position="top" class="safety-form" @submit.prevent="submitSafetyProfile">
          <el-form-item label="过敏原">
            <el-select
              v-model="safetyForm.allergens"
              multiple
              allow-create
              filterable
              default-first-option
              placeholder="输入后按回车添加，例如花生、牛奶"
            />
            <p class="field-help">命中的菜品不得进入正常推荐。</p>
          </el-form-item>
          <el-form-item label="长期明确忌口">
            <el-select
              v-model="safetyForm.avoidances"
              multiple
              allow-create
              filterable
              default-first-option
              placeholder="输入后按回车添加，例如不吃香菜"
            />
            <p class="field-help">仅填写长期限制，当餐偏好请在智能食堂中说明。</p>
          </el-form-item>
          <el-button native-type="submit" type="primary">保存安全档案</el-button>
        </el-form>
      </section>

      <section v-else-if="activeSection === 'authorization'" class="profile-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-label">Privacy controls</p>
            <h2>AI 数据授权</h2>
          </div>
          <span class="status-pill">默认不授权</span>
        </div>
        <p class="panel-description">四类数据默认不授权。每项授权可以独立开启或撤回。</p>
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
      </section>

      <section v-else class="profile-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-label">Security ledger</p>
            <h2>最近安全记录</h2>
          </div>
        </div>
        <el-empty v-if="auditEvents.length === 0" description="暂无记录" />
        <el-table v-else :data="auditEvents" stripe>
          <el-table-column prop="eventType" label="事件" min-width="170" />
          <el-table-column prop="outcome" label="结果" width="100" />
          <el-table-column prop="occurredAt" label="时间" min-width="210" />
        </el-table>
      </section>
    </div>
  </section>
</template>
