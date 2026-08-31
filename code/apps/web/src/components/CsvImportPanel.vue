<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { commitCsv, validateCsv } from '../api/management'
import type { ImportPreview, ResourceSchema } from '../types/management'

const props = defineProps<{ open: boolean; schema: ResourceSchema }>()
const emit = defineEmits<{ close: []; imported: [] }>()

const csvContent = ref('')
const preview = ref<ImportPreview | null>(null)
const loading = ref(false)

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      csvContent.value = `${props.schema.csvHeader}\n`
      preview.value = null
    }
  },
)

async function readFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv') || file.size > 524_288) {
    ElMessage.warning('请选择不超过 512KB 的 CSV 文件')
    input.value = ''
    return
  }
  csvContent.value = await file.text()
  preview.value = null
}

async function validate(): Promise<void> {
  loading.value = true
  try {
    preview.value = await validateCsv(props.schema.type, csvContent.value)
    ElMessage.success(
      preview.value.errors.length ? '校验完成，请修正错误' : '校验通过，可以确认入库',
    )
  } catch (error) {
    ElMessage.error(errorMessage(error, 'CSV 校验失败，请检查文件内容'))
  } finally {
    loading.value = false
  }
}

async function commit(): Promise<void> {
  loading.value = true
  try {
    const result = await commitCsv(props.schema.type, csvContent.value)
    preview.value = result
    if (!result.committed) {
      ElMessage.warning('资料未入库，请先修正全部错误')
      return
    }
    ElMessage.success(`已导入 ${result.validRows} 条${props.schema.label}资料`)
    emit('imported')
  } catch (error) {
    ElMessage.error(errorMessage(error, 'CSV 导入失败，请稍后重试'))
  } finally {
    loading.value = false
  }
}

function downloadTemplate(): void {
  const blob = new Blob([`${props.schema.csvHeader}\n`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${props.schema.type.toLowerCase()}-template.csv`
  anchor.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <el-dialog
    :model-value="open"
    :title="`批量导入${schema.label}`"
    width="min(820px, 94vw)"
    @close="emit('close')"
  >
    <div class="import-guide">
      <strong>先校验，再确认入库</strong>
      <p>文件应为 UTF-8 CSV，最多 200 行、512KB；列表字段使用竖线“|”分隔。</p>
      <el-button plain @click="downloadTemplate">下载字段模板</el-button>
      <input type="file" accept=".csv,text/csv" aria-label="选择CSV文件" @change="readFile" />
    </div>
    <el-input v-model="csvContent" type="textarea" :rows="10" aria-label="CSV内容" />

    <section v-if="preview" class="import-result" aria-live="polite">
      <div class="import-summary">
        <span>总行数 {{ preview.totalRows }}</span>
        <span>有效 {{ preview.validRows }}</span>
        <span :class="{ danger: preview.errors.length }">错误 {{ preview.errors.length }}</span>
      </div>
      <el-table v-if="preview.errors.length" :data="preview.errors" max-height="240">
        <el-table-column prop="row" label="行" width="70" />
        <el-table-column prop="field" label="字段" width="150" />
        <el-table-column prop="message" label="问题" min-width="260" />
      </el-table>
      <el-alert v-else title="所有记录均已通过字段、重复和引用关系校验" type="success" show-icon />
    </section>

    <template #footer>
      <el-button @click="emit('close')">关闭</el-button>
      <el-button :loading="loading" @click="validate">预校验</el-button>
      <el-button
        type="primary"
        :disabled="!preview || preview.errors.length > 0 || preview.committed"
        :loading="loading"
        @click="commit"
      >
        确认入库
      </el-button>
    </template>
  </el-dialog>
</template>
