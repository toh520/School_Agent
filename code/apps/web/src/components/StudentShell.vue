<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import type { MeData, Profile, UserSummary } from '../types/identity'

const props = defineProps<{ user: UserSummary; me: MeData }>()
const emit = defineEmits<{
  logout: []
  'profile-updated': [profile: Profile]
}>()

const route = useRoute()
const initials = computed(() => (props.user.nickname || props.user.username).slice(0, 1))

const navigation = [
  { name: 'home', label: '首页', path: '/home' },
  { name: 'canteen', label: '智能食堂', path: '/canteen' },
  { name: 'campus', label: '校园助手', path: '/campus' },
  { name: 'exam', label: '考试助手', path: '/exam' },
  { name: 'library', label: '智能图书馆', path: '/library' },
]
</script>

<template>
  <div class="student-app">
    <header class="student-header">
      <router-link class="student-brand" to="/home" aria-label="智慧校园首页">
        <span class="brand-seal">SA</span>
        <span><strong>智慧校园</strong><small>Student service map</small></span>
      </router-link>

      <nav class="student-nav" aria-label="学生服务导航">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.path"
          :class="{ active: route.name === item.name }"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <div class="student-account">
        <router-link class="profile-link" to="/profile">
          <span class="profile-avatar">
            <img v-if="me.profile.avatarUrl" :src="me.profile.avatarUrl" alt="" />
            <span v-else>{{ initials }}</span>
          </span>
          <span class="profile-copy">
            <strong>{{ user.nickname }}</strong>
            <small>{{ me.profile.studentNumber }}</small>
          </span>
        </router-link>
        <button class="logout-button" type="button" @click="emit('logout')">退出</button>
      </div>
    </header>

    <main class="student-main">
      <router-view v-slot="{ Component }">
        <transition name="page-shift" mode="out-in">
          <component
            :is="Component"
            :key="route.fullPath"
            :user="user"
            :me="me"
            @profile-updated="emit('profile-updated', $event)"
          />
        </transition>
      </router-view>
    </main>
  </div>
</template>
