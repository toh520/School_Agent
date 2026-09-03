<script setup lang="ts">
import type { MeData, UserSummary } from '../types/identity'

defineProps<{ user: UserSummary; me: MeData }>()
</script>

<template>
  <section class="module-page module-exam" aria-labelledby="exam-title">
    <header class="module-hero">
      <div>
        <p class="page-kicker">Exam assistant · 考试与规划</p>
        <h1 id="exam-title">先记清考试，再决定怎么复习。</h1>
        <p>考试记录不依赖 AI；只有你主动发起时，助手才会生成复习计划。</p>
      </div>
      <span class="module-emblem" aria-hidden="true">考</span>
    </header>

    <div class="exam-board">
      <section class="module-panel next-exam-card">
        <p class="panel-label">最近一场</p>
        <span class="empty-number">—</span>
        <h2>还没有考试记录</h2>
        <p>后续可记录科目、时间和备注，系统会自动按时间排序。</p>
        <el-button type="primary" disabled>添加考试</el-button>
      </section>
      <section class="module-panel plan-preview-card">
        <p class="panel-label">复习计划书</p>
        <h2>需要时，再请 AI 规划</h2>
        <ol>
          <li><span>1</span>选择一场已记录的考试</li>
          <li><span>2</span>补充范围、掌握情况和可用时间</li>
          <li><span>3</span>确认并保存生成的计划书</li>
        </ol>
        <span class="status-pill">等待考试业务接口</span>
      </section>
    </div>
  </section>
</template>
