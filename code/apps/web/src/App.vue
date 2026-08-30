<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchSystemHealth } from './api/health'
import type { SystemHealth } from './types/api'

const health = ref<SystemHealth | null>(null)
const requestId = ref('')
const errorMessage = ref('')
const loading = ref(false)

const isHealthy = computed(() => health.value?.status === 'UP')

async function refreshHealth(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetchSystemHealth()
    health.value = response.data
    requestId.value = response.requestId
  } catch {
    health.value = null
    errorMessage.value = '无法连接核心服务，请确认 Java、Python 和 PostgreSQL 已启动。'
  } finally {
    loading.value = false
  }
}

onMounted(refreshHealth)
</script>

<template>
  <main class="page-shell">
    <section class="health-card" aria-labelledby="page-title">
      <p class="eyebrow">M01 · 工程基础</p>
      <h1 id="page-title">智慧校园智能体系统</h1>
      <p class="intro">此页面仅验证浏览器、Java、Python 与 PostgreSQL 的公共健康链路。</p>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <div v-else-if="health" class="summary" data-testid="health-summary">
        <el-tag :type="isHealthy ? 'success' : 'danger'" size="large">
          {{ isHealthy ? '基础链路正常' : '基础链路异常' }}
        </el-tag>
        <dl class="service-grid">
          <div>
            <dt>Java 核心服务</dt>
            <dd>{{ health.coreService.status }}</dd>
          </div>
          <div>
            <dt>Python Agent 服务</dt>
            <dd>{{ health.agentService.status }}</dd>
          </div>
          <div>
            <dt>PostgreSQL / pgvector</dt>
            <dd>{{ health.database.status }}</dd>
          </div>
        </dl>
        <p class="request-id">请求标识：{{ requestId }}</p>
      </div>

      <el-skeleton v-else :rows="3" animated />
      <el-button type="primary" :loading="loading" @click="refreshHealth">重新检查</el-button>
    </section>
  </main>
</template>
