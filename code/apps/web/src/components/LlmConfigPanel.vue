<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { fetchResources, updateResource } from '../api/management'
import type { ManagedResource } from '../types/management'

interface RuntimeConfig {
  provider: string
  baseUrl: string
  model: string
  timeoutSeconds: number
  maxRetries: number
}

const loading = ref(true)
const saving = ref(false)
const record = ref<ManagedResource | null>(null)
const form = reactive<RuntimeConfig>({
  provider: 'siliconflow',
  baseUrl: 'https://api.siliconflow.cn/v1',
  model: 'deepseek-ai/DeepSeek-V4-Flash',
  timeoutSeconds: 180,
  maxRetries: 2,
})

const modelOptions = [
  'deepseek-ai/DeepSeek-V4-Flash',
  'Qwen/Qwen3.5-4B',
  'Qwen/Qwen3.5-9B',
  'Qwen/Qwen3.5-27B',
  'Qwen/Qwen3.5-35B-A3B',
  'Qwen/Qwen3.5-122B-A10B',
  'Qwen/Qwen3.5-397B-A17B',
]

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

async function load(): Promise<void> {
  loading.value = true
  try {
    const page = await fetchResources('SYSTEM_CONFIG', 'LLM_RUNTIME', 0, 'ACTIVE')
    const current = page.items.find((item) => item.values.code === 'LLM_RUNTIME') ?? null
    if (!current) throw new Error('未找到大模型运行配置，请先执行数据库迁移')
    record.value = current
    const parsed = JSON.parse(String(current.values.configValue || '{}')) as Partial<RuntimeConfig>
    form.provider = parsed.provider || form.provider
    form.baseUrl = parsed.baseUrl || form.baseUrl
    form.model = parsed.model || form.model
    form.timeoutSeconds = Number(parsed.timeoutSeconds || form.timeoutSeconds)
    form.maxRetries = Number(parsed.maxRetries ?? form.maxRetries)
  } catch (error) {
    ElMessage.error(errorMessage(error, '大模型配置加载失败'))
  } finally {
    loading.value = false
  }
}

async function save(): Promise<void> {
  if (!record.value) return
  if (!/^https?:\/\//.test(form.baseUrl)) {
    ElMessage.warning('接口地址必须以 http:// 或 https:// 开头')
    return
  }
  saving.value = true
  try {
    await updateResource('SYSTEM_CONFIG', record.value.id, {
      ...record.value.values,
      code: 'LLM_RUNTIME',
      name: '大模型运行配置',
      configValue: JSON.stringify(form),
      description: '管理端维护的非敏感模型运行参数，下一次 AI 请求立即生效。',
      source: '智能服务运行配置',
    })
    ElMessage.success(`已切换为 ${form.model}，下一次 AI 请求生效`)
    await load()
  } catch (error) {
    ElMessage.error(errorMessage(error, '大模型配置保存失败'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="llm-config-panel" v-loading="loading">
    <div class="llm-status-card">
      <p>当前生效模型</p>
      <strong>{{ form.model }}</strong>
      <span>配置保存后无需重启，下一次 AI 请求自动读取。</span>
      <dl>
        <div>
          <dt>服务来源</dt>
          <dd>硅基流动</dd>
        </div>
        <div>
          <dt>接口协议</dt>
          <dd>OpenAI 兼容</dd>
        </div>
        <div>
          <dt>密钥状态</dt>
          <dd>由服务器环境变量托管</dd>
        </div>
      </dl>
      <el-alert
        title="API Key 不会在管理端回显或写入公共配置，修改密钥仍需更新本机环境变量。"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <el-form label-position="top" class="llm-runtime-form" @submit.prevent="save">
      <div class="llm-form-heading">
        <div>
          <small>模型路由</small>
          <h2>调整下一次推理使用的模型</h2>
        </div>
        <el-tag type="success" effect="plain">动态生效</el-tag>
      </div>
      <el-form-item label="模型服务商">
        <el-select v-model="form.provider">
          <el-option label="硅基流动" value="siliconflow" />
        </el-select>
      </el-form-item>
      <el-form-item label="接口基础地址">
        <el-input v-model="form.baseUrl" placeholder="https://api.siliconflow.cn/v1" />
        <p class="field-help">填写到版本路径即可，系统会自动调用对话补全接口。</p>
      </el-form-item>
      <el-form-item label="模型名称">
        <el-select
          v-model="form.model"
          filterable
          allow-create
          default-first-option
          placeholder="选择或输入硅基流动模型名称"
        >
          <el-option v-for="model in modelOptions" :key="model" :label="model" :value="model" />
        </el-select>
        <p class="field-help">支持直接输入后续新增的模型标识，不受当前下拉列表限制。</p>
      </el-form-item>
      <div class="llm-number-grid">
        <el-form-item label="单次请求超时（秒）">
          <el-input-number v-model="form.timeoutSeconds" :min="5" :max="180" />
        </el-form-item>
        <el-form-item label="失败重试次数">
          <el-input-number v-model="form.maxRetries" :min="0" :max="5" />
        </el-form-item>
      </div>
      <div class="llm-save-note">
        <span>切换前请确认模型支持文本对话和 JSON 结构化输出。</span>
        <el-button type="primary" native-type="submit" :loading="saving">保存并切换模型</el-button>
      </div>
    </el-form>
  </section>
</template>
