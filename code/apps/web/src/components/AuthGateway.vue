<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { login, registerStudent } from '../api/auth'
import type { RegisterForm, UserSummary } from '../types/identity'

const emit = defineEmits<{ authenticated: [user: UserSummary] }>()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const errorMessage = ref('')
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive<RegisterForm>({
  studentNumber: '',
  phone: '',
  realName: '',
  username: '',
  password: '',
  confirmPassword: '',
})

function switchMode(nextMode: 'login' | 'register'): void {
  mode.value = nextMode
  errorMessage.value = ''
}

function apiError(error: any, fallback: string): string {
  return error?.response?.data?.error?.message ?? fallback
}

async function submitLogin(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const tokens = await login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    emit('authenticated', tokens.user)
  } catch (error: any) {
    errorMessage.value = apiError(error, '登录失败，请检查账号和密码。')
  } finally {
    loading.value = false
  }
}

async function submitRegistration(): Promise<void> {
  errorMessage.value = ''
  if (registerForm.password !== registerForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    const tokens = await registerStudent(registerForm)
    ElMessage.success('注册成功，已进入个人中心')
    emit('authenticated', tokens.user)
  } catch (error: any) {
    errorMessage.value = apiError(error, '注册失败，请检查填写的信息。')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="identity-gateway">
    <section class="identity-story" aria-labelledby="product-title">
      <div class="school-mark" aria-hidden="true">SA</div>
      <p class="section-label">School agent</p>
      <h1 id="product-title">智慧校园<br />伴你学习与生活</h1>
      <p class="story-copy">
        连接考试规划、食堂推荐、图书查询与校园问答，让常用校园服务集中在一个入口。
      </p>

      <div class="service-map" aria-label="校园智能助手服务范围">
        <p class="service-map-title">校园智能助手</p>
        <ul>
          <li><span>学习规划</span><strong>梳理考试安排与复习重点</strong></li>
          <li><span>校园生活</span><strong>获得食堂与饮食建议</strong></li>
          <li><span>图书查询</span><strong>查找馆藏与阅读方向</strong></li>
          <li><span>校园问答</span><strong>快速获取学校相关信息</strong></li>
        </ul>
      </div>
      <p class="story-note">登录后可在个人中心管理资料、偏好与数据授权。</p>
    </section>

    <section class="auth-workbench">
      <div class="auth-panel">
        <div class="mode-switch" role="tablist" aria-label="身份入口">
          <button
            role="tab"
            :aria-selected="mode === 'login'"
            :class="{ active: mode === 'login' }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            role="tab"
            :aria-selected="mode === 'register'"
            :class="{ active: mode === 'register' }"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>

        <Transition name="form-shift" mode="out-in">
          <section v-if="mode === 'login'" key="login" aria-labelledby="login-title">
            <p class="section-label">Account access</p>
            <h2 id="login-title">欢迎回来</h2>
            <p class="form-intro">使用你的账号继续访问个人中心。</p>
            <el-alert
              v-if="errorMessage"
              :title="errorMessage"
              type="error"
              :closable="false"
              show-icon
            />
            <el-form label-position="top" @submit.prevent="submitLogin">
              <el-form-item label="账号">
                <el-input
                  v-model="loginForm.username"
                  autocomplete="username"
                  maxlength="64"
                  placeholder="请输入账号"
                />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  autocomplete="current-password"
                  maxlength="72"
                  show-password
                  placeholder="请输入密码"
                />
              </el-form-item>
              <el-button native-type="submit" type="primary" :loading="loading" class="full-button">
                登录
              </el-button>
            </el-form>
            <button class="text-action" @click="switchMode('register')">
              还没有账号？创建学生账号
            </button>
          </section>

          <section v-else key="register" aria-labelledby="register-title">
            <p class="section-label">Student registration</p>
            <h2 id="register-title">创建学生账号</h2>
            <p class="form-intro">请使用本人的学号、姓名和手机号完成注册。</p>
            <el-alert
              v-if="errorMessage"
              :title="errorMessage"
              type="error"
              :closable="false"
              show-icon
            />
            <el-form label-position="top" @submit.prevent="submitRegistration">
              <div class="registration-grid">
                <el-form-item label="学号">
                  <el-input
                    v-model="registerForm.studentNumber"
                    inputmode="numeric"
                    maxlength="20"
                    placeholder="6–20位数字"
                  />
                </el-form-item>
                <el-form-item label="姓名">
                  <el-input
                    v-model="registerForm.realName"
                    maxlength="50"
                    placeholder="请输入姓名"
                  />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input
                    v-model="registerForm.phone"
                    inputmode="tel"
                    maxlength="11"
                    placeholder="11位手机号"
                  />
                </el-form-item>
                <el-form-item label="登录账号">
                  <el-input
                    v-model="registerForm.username"
                    autocomplete="username"
                    maxlength="32"
                    placeholder="字母、数字或下划线"
                  />
                </el-form-item>
                <el-form-item label="设置密码">
                  <el-input
                    v-model="registerForm.password"
                    type="password"
                    autocomplete="new-password"
                    maxlength="72"
                    show-password
                    placeholder="至少8个字符"
                  />
                </el-form-item>
                <el-form-item label="确认密码">
                  <el-input
                    v-model="registerForm.confirmPassword"
                    type="password"
                    autocomplete="new-password"
                    maxlength="72"
                    show-password
                    placeholder="再次输入密码"
                  />
                </el-form-item>
              </div>
              <el-button native-type="submit" type="primary" :loading="loading" class="full-button">
                创建账号
              </el-button>
            </el-form>
            <button class="text-action" @click="switchMode('login')">已有账号？返回登录</button>
          </section>
        </Transition>
      </div>
    </section>
  </main>
</template>
