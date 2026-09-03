<script setup lang="ts">
import { computed } from 'vue'

import type { MeData, UserSummary } from '../types/identity'

const props = defineProps<{ user: UserSummary; me: MeData }>()

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 11) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const services = [
  {
    key: 'canteen',
    mark: '食',
    title: '智能食堂',
    description: '查看今日餐品，或让 AI 按本次需求组合一餐。',
    path: '/canteen',
    status: '下一阶段开发',
  },
  {
    key: 'campus',
    mark: '问',
    title: '校园助手',
    description: '围绕校园办事与公告，发起一场有依据的问答。',
    path: '/campus',
    status: '对话底座可用',
  },
  {
    key: 'exam',
    mark: '考',
    title: '考试助手',
    description: '记录考试安排，主动生成可执行的复习计划。',
    path: '/exam',
    status: '界面已规划',
  },
  {
    key: 'library',
    mark: '书',
    title: '智能图书馆',
    description: '查询真实馆藏，也可以按当次目标请 AI 选书。',
    path: '/library',
    status: '界面已规划',
  },
]
</script>

<template>
  <section class="home-page" aria-labelledby="home-title">
    <header class="home-intro">
      <div>
        <p class="page-kicker">Campus routes · 学生服务地图</p>
        <h1 id="home-title">{{ greeting }}，{{ user.nickname }}</h1>
        <p>今天想去哪里？从一个明确的校园任务开始。</p>
      </div>
      <router-link class="home-profile-card" to="/profile" aria-label="进入个人中心">
        <div class="campus-card-topline"><span>STUDENT PASS</span><span>智慧校园</span></div>
        <div class="campus-card-name">
          <span class="campus-card-avatar">{{ user.nickname.slice(0, 1) }}</span>
          <div>
            <strong>{{ me.profile.realName }}</strong
            ><small>{{ user.username }}</small>
          </div>
        </div>
        <div class="campus-card-number">
          <span>学号</span><strong>{{ me.profile.studentNumber }}</strong>
        </div>
      </router-link>
    </header>

    <div class="campus-map" aria-label="四个校园服务模块">
      <router-link
        v-for="service in services"
        :key="service.key"
        :to="service.path"
        :class="['service-destination', `destination-${service.key}`]"
      >
        <span class="destination-mark">{{ service.mark }}</span>
        <span class="destination-copy">
          <small>{{ service.status }}</small>
          <strong>{{ service.title }}</strong>
          <span>{{ service.description }}</span>
        </span>
        <span class="destination-arrow" aria-hidden="true">↗</span>
      </router-link>
    </div>

    <footer class="home-footnote">
      <span class="safety-dot"></span>
      <p>个人档案只保存长期稳定的信息。每餐口味、预算和目标将在智能食堂中按本次需求填写。</p>
    </footer>
  </section>
</template>
