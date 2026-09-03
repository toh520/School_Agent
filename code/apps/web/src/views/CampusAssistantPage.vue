<script setup lang="ts">
import AgentWorkspace from '../components/AgentWorkspace.vue'
import type { MeData, UserSummary } from '../types/identity'

defineProps<{ user: UserSummary; me: MeData }>()
</script>

<template>
  <section class="module-page module-campus" aria-labelledby="campus-title">
    <header class="compact-module-header">
      <div>
        <p class="page-kicker">Campus assistant · 校园问答</p>
        <h1 id="campus-title">校内信息，问得清楚，答得有据。</h1>
        <p>基于校内知识库检索规章、办事流程与校园服务信息，并清楚区分可靠资料与一般参考。</p>
      </div>
      <span class="module-emblem" aria-hidden="true">问</span>
    </header>
    <div class="agent-module-host agent-host">
      <AgentWorkspace />
    </div>
  </section>
</template>
