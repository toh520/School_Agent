<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createResource,
  deactivateResource,
  fetchAccounts,
  fetchOperationLogs,
  fetchResources,
  fetchSchemas,
  setAccountStatus,
  updateResource,
} from '../api/management'
import type { UserSummary } from '../types/identity'
import type {
  AccountSummary,
  ManagedResource,
  OperationLog,
  ResourceSchema,
  ResourceType,
} from '../types/management'
import CsvImportPanel from './CsvImportPanel.vue'
import ResourceEditor from './ResourceEditor.vue'

const props = defineProps<{ user: UserSummary }>()
const emit = defineEmits<{ logout: [] }>()

type AdminView = ResourceType | 'ACCOUNTS' | 'OPERATIONS'

const navigation: Array<{ title: string; items: Array<{ key: AdminView; label: string }> }> = [
  {
    title: '餐饮资料',
    items: [
      { key: 'CANTEEN', label: '食堂' },
      { key: 'STALL', label: '窗口' },
      { key: 'INGREDIENT', label: '食材' },
      { key: 'DISH', label: '菜品' },
    ],
  },
  {
    title: '图书资料',
    items: [
      { key: 'BOOK', label: '书目' },
      { key: 'HOLDING', label: '馆藏' },
    ],
  },
  {
    title: '校园资料',
    items: [
      { key: 'KNOWLEDGE', label: '校园公告' },
      { key: 'SYSTEM_CONFIG', label: '公共配置' },
    ],
  },
  {
    title: '系统管理',
    items: [
      { key: 'ACCOUNTS', label: '账号状态' },
      { key: 'OPERATIONS', label: '操作记录' },
    ],
  },
]

const activeView = ref<AdminView>('CANTEEN')
const schemas = ref<ResourceSchema[]>([])
const resources = ref<ManagedResource[]>([])
const accounts = ref<AccountSummary[]>([])
const operationLogs = ref<OperationLog[]>([])
const query = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const resourceStatus = ref<ManagedResource['status']>('ACTIVE')
const loading = ref(false)
const editorOpen = ref(false)
const importOpen = ref(false)
const selectedResource = ref<ManagedResource | null>(null)
const saving = ref(false)

const activeSchema = computed(
  () => schemas.value.find((schema) => schema.type === activeView.value) ?? null,
)
const isResourceView = computed(
  () => activeView.value !== 'ACCOUNTS' && activeView.value !== 'OPERATIONS',
)

const actionLabels: Record<string, string> = {
  CREATE: '新增',
  UPDATE: '编辑',
  DEACTIVATE: '停用',
  IMPORT: '批量导入',
  ACCOUNT_STATUS: '账号状态',
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

async function loadActive(): Promise<void> {
  loading.value = true
  try {
    const pageIndex = currentPage.value - 1
    if (activeView.value === 'ACCOUNTS') {
      const page = await fetchAccounts(query.value, pageIndex)
      accounts.value = page.items
      total.value = page.total
    } else if (activeView.value === 'OPERATIONS') {
      const page = await fetchOperationLogs(pageIndex)
      operationLogs.value = page.items
      total.value = page.total
    } else {
      const page = await fetchResources(
        activeView.value,
        query.value,
        pageIndex,
        resourceStatus.value,
      )
      resources.value = page.items
      total.value = page.total
    }
  } catch (error) {
    ElMessage.error(errorMessage(error, '资料加载失败，请稍后重试'))
  } finally {
    loading.value = false
  }
}

async function selectView(view: AdminView): Promise<void> {
  activeView.value = view
  query.value = ''
  currentPage.value = 1
  resourceStatus.value = 'ACTIVE'
  await loadActive()
}

async function searchActive(): Promise<void> {
  currentPage.value = 1
  await loadActive()
}

async function changePage(page: number): Promise<void> {
  currentPage.value = page
  await loadActive()
}

async function changeResourceStatus(): Promise<void> {
  currentPage.value = 1
  await loadActive()
}

function openCreate(): void {
  selectedResource.value = null
  editorOpen.value = true
}

function openEdit(resource: ManagedResource): void {
  selectedResource.value = resource
  editorOpen.value = true
}

async function saveResource(values: Record<string, unknown>): Promise<void> {
  if (!activeSchema.value) return
  saving.value = true
  try {
    if (selectedResource.value) {
      await updateResource(activeSchema.value.type, selectedResource.value.id, values)
      ElMessage.success('资料已更新')
    } else {
      await createResource(activeSchema.value.type, values)
      ElMessage.success('资料已创建')
      resourceStatus.value = 'ACTIVE'
      currentPage.value = 1
    }
    editorOpen.value = false
    await loadActive()
  } catch (error) {
    ElMessage.error(errorMessage(error, '资料保存失败，请检查填写内容'))
  } finally {
    saving.value = false
  }
}

async function deactivate(resource: ManagedResource): Promise<void> {
  if (!activeSchema.value) return
  try {
    await ElMessageBox.confirm(
      `停用“${String(resource.values.name)}”后，后续业务默认不再使用该资料。`,
      '确认停用资料',
      { type: 'warning', confirmButtonText: '确认停用', cancelButtonText: '取消' },
    )
    await deactivateResource(activeSchema.value.type, resource.id)
    ElMessage.success('资料已停用')
    if (resources.value.length === 1 && currentPage.value > 1) currentPage.value -= 1
    await loadActive()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(errorMessage(error, '资料停用失败'))
    }
  }
}

async function changeAccountStatus(account: AccountSummary): Promise<void> {
  const next = account.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE'
  try {
    await ElMessageBox.confirm(
      `${next === 'DISABLED' ? '禁用' : '启用'}账号“${account.username}”？`,
      '确认账号状态',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' },
    )
    await setAccountStatus(account.id, next)
    ElMessage.success('账号状态已更新')
    await loadActive()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(errorMessage(error, '账号状态更新失败'))
    }
  }
}

async function handleImported(): Promise<void> {
  importOpen.value = false
  resourceStatus.value = 'ACTIVE'
  currentPage.value = 1
  await loadActive()
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function actionLabel(action: string): string {
  return actionLabels[action] ?? action
}

function resourceTypeLabel(type: string): string {
  if (type === 'ACCOUNT') return '账号'
  return schemas.value.find((schema) => schema.type === type)?.label ?? type
}

onMounted(async () => {
  try {
    schemas.value = await fetchSchemas()
    await loadActive()
  } catch (error) {
    ElMessage.error(errorMessage(error, '管理台初始化失败'))
  }
})
</script>

<template>
  <main class="admin-shell">
    <header class="admin-topbar">
      <div>
        <p class="eyebrow">School data registry</p>
        <strong>校园资料管理台</strong>
      </div>
      <div class="admin-identity">
        <span>{{ props.user.nickname }}</span>
        <el-tag size="small" effect="dark">信息资料管理员</el-tag>
        <el-button plain @click="emit('logout')">安全退出</el-button>
      </div>
    </header>

    <div class="admin-layout">
      <aside class="admin-rail" aria-label="资料分类导航">
        <section v-for="group in navigation" :key="group.title">
          <p>{{ group.title }}</p>
          <button
            v-for="item in group.items"
            :key="item.key"
            :class="{ active: activeView === item.key }"
            @click="selectView(item.key)"
          >
            {{ item.label }}
          </button>
        </section>
      </aside>

      <section class="registry-canvas" v-loading="loading">
        <header class="registry-heading">
          <div>
            <p class="eyebrow">统一信息资料管理</p>
            <h1 v-if="activeSchema">
              {{
                activeSchema.type === 'KNOWLEDGE' ? activeSchema.label : `${activeSchema.label}资料`
              }}
            </h1>
            <h1 v-else-if="activeView === 'ACCOUNTS'">账号状态</h1>
            <h1 v-else>操作记录</h1>
            <p>{{ total }} 条可管理记录</p>
          </div>
          <div v-if="isResourceView" class="registry-actions">
            <el-input
              v-model="query"
              clearable
              placeholder="按编码、名称或内容搜索"
              aria-label="搜索资料"
              @keyup.enter="searchActive"
            />
            <el-select
              v-model="resourceStatus"
              class="registry-filter"
              aria-label="资料状态"
              @change="changeResourceStatus"
            >
              <el-option label="有效资料" value="ACTIVE" />
              <el-option label="已停用资料" value="INACTIVE" />
            </el-select>
            <el-button @click="searchActive">搜索</el-button>
            <el-button @click="importOpen = true">批量导入</el-button>
            <el-button type="primary" @click="openCreate">新增资料</el-button>
          </div>
          <div v-else-if="activeView === 'ACCOUNTS'" class="registry-actions">
            <el-input
              v-model="query"
              clearable
              placeholder="搜索账号或昵称"
              aria-label="搜索账号"
              @keyup.enter="searchActive"
            />
            <el-button @click="searchActive">搜索</el-button>
          </div>
        </header>

        <el-empty
          v-if="isResourceView && !resources.length && !loading"
          :description="
            resourceStatus === 'INACTIVE' ? '暂无已停用资料' : '暂无资料，可新增或批量导入'
          "
        />
        <el-table v-else-if="isResourceView" :data="resources" row-key="id">
          <el-table-column label="资料" min-width="230">
            <template #default="scope">
              <strong>{{ scope.row.values.name }}</strong>
              <code>{{ scope.row.values.code }}</code>
            </template>
          </el-table-column>
          <el-table-column label="完整度" width="180">
            <template #default="scope">
              <div class="table-quality">
                <el-progress :percentage="scope.row.completeness" :stroke-width="6" />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="来源" min-width="180">
            <template #default="scope">{{ scope.row.values.source }}</template>
          </el-table-column>
          <el-table-column label="更新时间" width="170">
            <template #default="scope">{{ formatTime(scope.row.updatedAt) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-tag v-if="scope.row.status === 'INACTIVE'" size="small" type="info">
                已停用
              </el-tag>
              <template v-else>
                <el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button>
                <el-button link type="danger" @click="deactivate(scope.row)">停用</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>

        <el-table v-else-if="activeView === 'ACCOUNTS'" :data="accounts" row-key="id">
          <el-table-column prop="username" label="账号" min-width="170" />
          <el-table-column prop="nickname" label="昵称" min-width="170" />
          <el-table-column label="角色" width="150">
            <template #default="scope">{{
              scope.row.role === 'STUDENT' ? '学生' : '信息资料管理员'
            }}</template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'ACTIVE' ? 'success' : 'info'">
                {{ scope.row.status === 'ACTIVE' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="170">
            <template #default="scope">{{ formatTime(scope.row.createdAt) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.id === props.user.id" size="small" type="info">
                当前账号
              </el-tag>
              <el-button v-else link type="primary" @click="changeAccountStatus(scope.row)">
                {{ scope.row.status === 'ACTIVE' ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-table v-else :data="operationLogs" row-key="id">
          <el-table-column label="动作" width="110">
            <template #default="scope">
              <el-tag size="small" effect="plain">{{ actionLabel(scope.row.action) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="操作内容" min-width="180" />
          <el-table-column label="操作者" min-width="240">
            <template #default="scope">
              <div class="log-identity">
                <strong>{{ scope.row.actorUsername || '账号已删除' }}</strong>
                <code>{{ scope.row.actorUserId || '—' }}</code>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="作用对象" min-width="190">
            <template #default="scope">
              <span>{{ resourceTypeLabel(scope.row.resourceType) }}</span>
              <code>{{ scope.row.resourceCode || scope.row.resourceId || '—' }}</code>
            </template>
          </el-table-column>
          <el-table-column label="请求编号" min-width="210">
            <template #default="scope">
              <code class="log-request">{{ scope.row.requestId || '—' }}</code>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="180">
            <template #default="scope">{{ formatTime(scope.row.occurredAt) }}</template>
          </el-table-column>
        </el-table>

        <footer v-if="total > pageSize" class="registry-pagination">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            @current-change="changePage"
          />
        </footer>
      </section>
    </div>

    <ResourceEditor
      v-if="activeSchema"
      :open="editorOpen"
      :schema="activeSchema"
      :resource="selectedResource"
      :saving="saving"
      @close="editorOpen = false"
      @save="saveResource"
    />
    <CsvImportPanel
      v-if="activeSchema"
      :open="importOpen"
      :schema="activeSchema"
      @close="importOpen = false"
      @imported="handleImported"
    />
  </main>
</template>
