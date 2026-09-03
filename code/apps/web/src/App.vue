<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { logout, restoreSession } from './api/auth'
import { fetchMe } from './api/user'
import AdminWorkspace from './components/AdminWorkspace.vue'
import AuthGateway from './components/AuthGateway.vue'
import StudentShell from './components/StudentShell.vue'
import type { MeData, Profile, UserSummary } from './types/identity'

const router = useRouter()
const currentUser = ref<UserSummary | null>(null)
const me = ref<MeData | null>(null)
const isStudent = computed(() => currentUser.value?.role === 'STUDENT')

async function loadMe(): Promise<void> {
  me.value = await fetchMe()
}

async function handleAuthenticated(user: UserSummary): Promise<void> {
  currentUser.value = user
  await loadMe()
  if (user.role === 'STUDENT') await router.replace('/home')
}

async function submitLogout(): Promise<void> {
  await logout()
  currentUser.value = null
  me.value = null
  await router.replace('/home')
  ElMessage.success('已安全退出')
}

function handleProfileUpdated(profile: Profile): void {
  if (me.value) me.value.profile = profile
  if (currentUser.value) currentUser.value.nickname = profile.nickname
}

onMounted(async () => {
  const tokens = await restoreSession()
  if (!tokens) return
  currentUser.value = tokens.user
  await loadMe()
})
</script>

<template>
  <AuthGateway v-if="!currentUser" @authenticated="handleAuthenticated" />

  <AdminWorkspace v-else-if="!isStudent" :user="currentUser" @logout="submitLogout" />

  <StudentShell
    v-else-if="me"
    :user="currentUser"
    :me="me"
    @logout="submitLogout"
    @profile-updated="handleProfileUpdated"
  />
</template>
