<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

import type { ManagedResource, ResourceSchema } from '../types/management'

const props = defineProps<{
  open: boolean
  schema: ResourceSchema
  resource: ManagedResource | null
  saving: boolean
}>()

const emit = defineEmits<{
  close: []
  save: [values: Record<string, unknown>]
}>()

const form = reactive<Record<string, any>>({})

watch(
  () => [props.open, props.resource, props.schema] as const,
  () => {
    for (const key of Object.keys(form)) delete form[key]
    for (const field of props.schema.fields) {
      const current = props.resource?.values[field.key]
      form[field.key] = current ?? (field.kind === 'LIST' ? [] : '')
    }
  },
  { immediate: true },
)

const completeness = computed(() => {
  const tracked = props.schema.fields.filter((field) => field.required || field.recommended)
  const filled = tracked.filter((field) => !isBlank(form[field.key])).length
  return tracked.length ? Math.round((filled / tracked.length) * 100) : 100
})

function isBlank(value: unknown): boolean {
  return (
    value === null || value === undefined || value === '' || (Array.isArray(value) && !value.length)
  )
}

function submit(): void {
  const missing = props.schema.fields.find((field) => field.required && isBlank(form[field.key]))
  if (missing) {
    ElMessage.warning(`请填写必填项：${missing.label}`)
    return
  }
  emit('save', { ...form })
}
</script>

<template>
  <el-drawer
    :model-value="open"
    :title="resource ? `编辑${schema.label}` : `新增${schema.label}`"
    size="min(620px, 92vw)"
    @close="emit('close')"
  >
    <div class="quality-meter">
      <div>
        <span>资料完整度</span>
        <strong>{{ completeness }}%</strong>
      </div>
      <el-progress :percentage="completeness" :show-text="false" />
      <p>必填字段用于保证资料可用，推荐字段将提升后续推荐和问答质量。</p>
    </div>

    <el-form label-position="top" class="resource-form" @submit.prevent="submit">
      <el-form-item v-for="field in schema.fields" :key="field.key">
        <template #label>
          <span>{{ field.label }}</span>
          <em v-if="field.required">必填</em>
          <em v-else-if="field.recommended" class="recommended">推荐</em>
        </template>

        <el-input
          v-if="field.kind === 'TEXT' || field.kind === 'URL'"
          v-model="form[field.key]"
          :maxlength="field.kind === 'URL' ? 1000 : 300"
          :placeholder="field.help"
        />
        <el-input
          v-else-if="field.kind === 'LONG_TEXT'"
          v-model="form[field.key]"
          type="textarea"
          :rows="4"
          maxlength="20000"
          :placeholder="field.help"
          show-word-limit
        />
        <el-input-number
          v-else-if="field.kind === 'INTEGER' || field.kind === 'DECIMAL'"
          v-model="form[field.key]"
          :min="0"
          :precision="field.kind === 'DECIMAL' ? 2 : 0"
          controls-position="right"
        />
        <el-select
          v-else-if="field.kind === 'LIST'"
          v-model="form[field.key]"
          multiple
          filterable
          allow-create
          default-first-option
          :placeholder="field.help"
        />
        <el-select v-else v-model="form[field.key]" :placeholder="field.help">
          <el-option v-for="option in field.options" :key="option" :value="option" />
        </el-select>
        <p class="field-help">{{ field.help }}</p>
      </el-form-item>

      <div class="drawer-actions">
        <el-button @click="emit('close')">取消</el-button>
        <el-button type="primary" native-type="submit" :loading="saving">
          {{ resource ? '保存修改' : '创建资料' }}
        </el-button>
      </div>
    </el-form>
  </el-drawer>
</template>
