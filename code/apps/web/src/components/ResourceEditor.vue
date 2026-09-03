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

const optionLabels: Record<string, string> = {
  STAPLE: '主食',
  MEAT: '荤菜',
  VEGETABLE: '素菜',
  SOUP: '汤品',
  DRINK: '饮品',
  SNACK: '小吃',
  MAIN: '主菜',
  SIDE: '配菜',
  SOUP_DRINK: '汤饮',
  EXTRA: '加餐',
  NONE: '不辣',
  MILD: '微辣',
  MEDIUM: '中辣',
  HOT: '重辣',
  SMALL: '小份',
  STANDARD: '标准份',
  LARGE: '大份',
  AVAILABLE: '在售',
  UNAVAILABLE: '售罄',
  YES: '是',
  NO: '否',
  UNKNOWN: '未知',
  LOW: '较低',
  HIGH: '较高',
}

function optionLabel(fieldKey: string, option: string): string {
  if (['energyLevel', 'proteinLevel', 'carbLevel', 'oilLevel'].includes(fieldKey)) {
    return { UNKNOWN: '未知', LOW: '较低', MEDIUM: '适中', HIGH: '较高' }[option] ?? option
  }
  return optionLabels[option] ?? option
}

const visibleFields = computed(() =>
  props.schema.type === 'DISH' || props.schema.type === 'KNOWLEDGE'
    ? props.schema.fields.filter((field) => field.key !== 'code' && field.key !== 'source')
    : props.schema.fields,
)

watch(
  () => [props.open, props.resource, props.schema] as const,
  () => {
    for (const key of Object.keys(form)) delete form[key]
    for (const field of props.schema.fields) {
      const current = props.resource?.values[field.key]
      form[field.key] = current ?? (field.kind === 'LIST' ? [] : '')
    }
    if (props.schema.type === 'DISH') {
      form.code ||= `FOOD-${crypto.randomUUID().slice(0, 8).toUpperCase()}`
      form.source = '智能食堂餐品管理'
      form.energyLevel ||= 'UNKNOWN'
      form.proteinLevel ||= 'UNKNOWN'
      form.carbLevel ||= 'UNKNOWN'
      form.oilLevel ||= 'UNKNOWN'
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

function selectImage(event: Event, key: string): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  if (file.size > 1024 * 1024) {
    ElMessage.warning('测试阶段图片请控制在 1MB 以内')
    input.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form[key] = String(reader.result)
  }
  reader.readAsDataURL(file)
}
</script>

<template>
  <el-drawer
    :model-value="open"
    :title="resource ? `编辑${schema.label}` : `新增${schema.label}`"
    size="min(620px, 92vw)"
    @close="emit('close')"
  >
    <div v-if="schema.type !== 'KNOWLEDGE'" class="quality-meter">
      <div>
        <span>资料完整度</span>
        <strong>{{ completeness }}%</strong>
      </div>
      <el-progress :percentage="completeness" :show-text="false" />
      <p>必填字段用于保证资料可用，推荐字段将提升后续推荐和问答质量。</p>
    </div>

    <el-form label-position="top" class="resource-form" @submit.prevent="submit">
      <el-form-item v-for="field in visibleFields" :key="field.key">
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
        <div v-else-if="field.kind === 'IMAGE'" class="food-image-upload">
          <img v-if="form[field.key]" :src="form[field.key]" alt="餐品图片预览" />
          <div v-else class="food-image-placeholder">等待上传图片</div>
          <label class="food-image-picker">
            选择本地图片
            <input type="file" accept="image/*" @change="selectImage($event, field.key)" />
          </label>
        </div>
        <el-input
          v-else-if="field.kind === 'LONG_TEXT'"
          v-model="form[field.key]"
          type="textarea"
          :rows="schema.type === 'KNOWLEDGE' ? 12 : 4"
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
          <el-option
            v-for="option in field.options"
            :key="option"
            :label="optionLabel(field.key, option)"
            :value="option"
          />
        </el-select>
        <p class="field-help">{{ field.help }}</p>
      </el-form-item>

      <div class="drawer-actions">
        <el-button @click="emit('close')">取消</el-button>
        <el-button type="primary" native-type="submit" :loading="saving">
          {{ resource ? '保存修改' : schema.type === 'KNOWLEDGE' ? '保存到知识库' : '创建资料' }}
        </el-button>
      </div>
    </el-form>
  </el-drawer>
</template>
