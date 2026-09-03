<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createConversation,
  deleteConversation,
  fetchConversation,
  fetchConversations,
  regenerateTask,
  saveFeedback,
  streamMessage,
} from '../api/agent'
import type {
  AgentMessage,
  AgentStreamCallbacks,
  ConversationDetail,
  ConversationSummary,
  FeedbackCategory,
  PersistedTurn,
} from '../types/agent'

const starters = [
  '校园卡丢失后应该如何补办？',
  '学校奖学金申请需要什么材料？',
  '学生证明可以在哪里办理？',
  '校内常用办事服务有哪些？',
]

const conversations = ref<ConversationSummary[]>([])
const active = ref<ConversationDetail | null>(null)
const composer = ref('')
const sending = ref(false)
const statusLabel = ref('等待你的问题')
const trace = ref<{ label: string; state: 'active' | 'done' }[]>([])
const messageArea = ref<HTMLElement | null>(null)

const canSend = computed(() => composer.value.trim().length > 0 && !sending.value)

async function loadWorkspace(): Promise<void> {
  conversations.value = await fetchConversations()
  if (conversations.value.length === 0) {
    conversations.value = [await createConversation()]
  }
  await selectConversation(conversations.value[0].id)
}

async function selectConversation(id: string): Promise<void> {
  active.value = await fetchConversation(id)
  statusLabel.value = '等待你的问题'
  trace.value = []
  await scrollToLatest()
}

async function addConversation(): Promise<void> {
  const created = await createConversation()
  conversations.value.unshift(created)
  await selectConversation(created.id)
}

async function removeConversation(item: ConversationSummary): Promise<void> {
  await ElMessageBox.confirm('删除后，该会话及其任务轨迹将不再显示。', '删除会话', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
  })
  await deleteConversation(item.id)
  conversations.value = conversations.value.filter((conversation) => conversation.id !== item.id)
  if (active.value?.id === item.id) {
    if (conversations.value.length === 0) conversations.value = [await createConversation()]
    await selectConversation(conversations.value[0].id)
  }
  ElMessage.success('会话已删除')
}

async function submitMessage(): Promise<void> {
  if (!active.value || !canSend.value) return
  const content = composer.value.trim()
  composer.value = ''
  const conversationId = active.value.id
  active.value.messages.push(localMessage('USER', content))
  const assistant = localMessage('ASSISTANT', '')
  active.value.messages.push(assistant)
  sending.value = true
  trace.value = []
  await scrollToLatest()
  try {
    await streamMessage(conversationId, content, callbacks(assistant))
    await refreshActive(conversationId)
  } catch (error) {
    assistant.content = error instanceof Error ? error.message : '智能服务暂时无法响应'
    statusLabel.value = '本轮未完成，可以重新发送'
  } finally {
    sending.value = false
    conversations.value = await fetchConversations()
    await scrollToLatest()
  }
}

async function regenerate(message: AgentMessage): Promise<void> {
  if (!active.value || !message.taskId || sending.value) return
  const assistant = localMessage('ASSISTANT', '')
  active.value.messages.push(assistant)
  sending.value = true
  trace.value = []
  try {
    await regenerateTask(message.taskId, callbacks(assistant))
    await refreshActive(active.value.id)
  } catch (error) {
    assistant.content = error instanceof Error ? error.message : '重新生成失败'
  } finally {
    sending.value = false
    await scrollToLatest()
  }
}

async function feedback(message: AgentMessage, category: FeedbackCategory): Promise<void> {
  if (!message.resultVersionId) return
  await saveFeedback(message.resultVersionId, category)
  ElMessage.success('反馈已记录')
}

function callbacks(assistant: AgentMessage): AgentStreamCallbacks {
  return {
    onStatus(data) {
      statusLabel.value = data.label
      trace.value.forEach((item) => (item.state = 'done'))
      trace.value.push({ label: data.label, state: 'active' })
    },
    onIntent() {},
    onTool(data) {
      trace.value.forEach((item) => (item.state = 'done'))
      trace.value.push({
        label: data.status === 'SUCCESS' ? '条件与权限校验通过' : '条件或权限校验未通过',
        state: 'done',
      })
    },
    onContent(data) {
      assistant.content += data.delta
      void scrollToLatest()
    },
    onDone(data: PersistedTurn) {
      assistant.id = data.messageId
      assistant.taskId = data.taskId
      assistant.resultVersionId = data.resultVersionId
      assistant.intent = data.result.intent
      assistant.basis = data.result.basis
      assistant.limitations = data.result.limitations
      assistant.fallbackUsed = data.result.fallbackUsed
      statusLabel.value = data.result.status === 'NEEDS_INPUT' ? '等待补充信息' : '本轮已完成'
      trace.value.forEach((item) => (item.state = 'done'))
    },
  }
}

async function refreshActive(id: string): Promise<void> {
  active.value = await fetchConversation(id)
}

function localMessage(role: 'USER' | 'ASSISTANT', content: string): AgentMessage {
  return {
    id: `local-${Date.now()}-${role}`,
    role,
    content,
    sequenceNumber: (active.value?.messages.length ?? 0) + 1,
    resultVersionId: null,
    taskId: null,
    intent: null,
    fallbackUsed: false,
    basis: [],
    limitations: [],
    createdAt: new Date().toISOString(),
  }
}

async function scrollToLatest(): Promise<void> {
  await nextTick()
  if (messageArea.value) messageArea.value.scrollTop = messageArea.value.scrollHeight
}

function useStarter(value: string): void {
  composer.value = value
}

onMounted(() => void loadWorkspace())
</script>

<template>
  <section class="agent-workspace" aria-label="校园知识助手">
    <aside class="conversation-rail">
      <div class="rail-heading">
        <div>
          <span>CONVERSATIONS</span>
          <strong>我的会话</strong>
        </div>
        <button aria-label="新建会话" @click="addConversation">＋</button>
      </div>
      <div class="conversation-list">
        <article
          v-for="item in conversations"
          :key="item.id"
          :class="{ active: active?.id === item.id }"
          @click="selectConversation(item.id)"
        >
          <button class="conversation-title">{{ item.title }}</button>
          <span>校园知识问答</span>
          <button
            class="conversation-delete"
            aria-label="删除会话"
            @click.stop="removeConversation(item)"
          >
            ×
          </button>
        </article>
      </div>
    </aside>

    <section class="dialogue-desk">
      <header class="dialogue-header">
        <div>
          <p>Campus knowledge desk</p>
          <h2>{{ active?.title || '校园知识助手' }}</h2>
        </div>
        <span class="knowledge-stamp">校内知识库</span>
      </header>

      <div ref="messageArea" class="message-ledger" aria-live="polite">
        <div v-if="!active?.messages.length" class="agent-empty">
          <span class="agent-monogram">问</span>
          <h3>从一个校园问题开始</h3>
          <p>助手会优先检索校内知识库，并根据命中的资料回答；没有可靠资料时会明确说明。</p>
          <div class="starter-grid">
            <button v-for="starter in starters" :key="starter" @click="useStarter(starter)">
              {{ starter }}
            </button>
          </div>
        </div>

        <article
          v-for="message in active?.messages"
          :key="message.id"
          :class="['message-entry', message.role.toLowerCase()]"
        >
          <div class="message-author">{{ message.role === 'USER' ? '你' : '校园助手' }}</div>
          <div class="message-body">
            <p>{{ message.content || '正在生成…' }}</p>
            <div v-if="message.role === 'ASSISTANT' && message.basis.length" class="answer-notes">
              <span>依据：{{ message.basis.join(' · ') }}</span>
              <span v-if="message.limitations.length"
                >限制：{{ message.limitations.join('；') }}</span
              >
            </div>
            <div
              v-if="message.role === 'ASSISTANT' && message.resultVersionId"
              class="message-actions"
            >
              <button @click="feedback(message, 'HELPFUL')">有帮助</button>
              <button @click="feedback(message, 'UNHELPFUL')">没帮助</button>
              <button @click="feedback(message, 'INCORRECT')">内容错误</button>
              <button @click="feedback(message, 'OUTDATED')">信息过期</button>
              <button @click="regenerate(message)">重新生成</button>
            </div>
          </div>
        </article>
      </div>

      <form class="agent-composer" @submit.prevent="submitMessage">
        <el-input
          v-model="composer"
          type="textarea"
          :rows="3"
          maxlength="4000"
          resize="none"
          placeholder="请输入校园规定、办事流程或校园服务问题…"
          aria-label="向校园助手提问"
          @keydown.ctrl.enter="submitMessage"
        />
        <div>
          <span>Ctrl + Enter 发送</span>
          <el-button native-type="submit" type="primary" :loading="sending" :disabled="!canSend">
            发送问题
          </el-button>
        </div>
      </form>
    </section>

    <aside class="task-rail">
      <p class="task-kicker">本轮任务</p>
      <h3>{{ statusLabel }}</h3>
      <ol class="task-trace">
        <li v-for="(item, index) in trace" :key="`${item.label}-${index}`" :class="item.state">
          <span>{{ index + 1 }}</span>
          {{ item.label }}
        </li>
      </ol>
      <div class="boundary-note">
        <strong>回答边界</strong>
        <p>知识库未命中时，助手会明确提示，并将模型自身回答标注为一般性参考。</p>
      </div>
      <div class="knowledge-scope">
        <strong>知识库范围</strong>
        <ul>
          <li>校园规章与通知</li>
          <li>校内办事流程</li>
          <li>校园服务说明</li>
        </ul>
      </div>
    </aside>
  </section>
</template>
