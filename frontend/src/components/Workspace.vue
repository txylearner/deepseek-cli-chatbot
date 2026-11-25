<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import AppSidebar from './AppSidebar.vue'
import ChatHeader from './ChatHeader.vue'
import ChatComposer from './ChatComposer.vue'
import MessageList from './MessageList.vue'
import { deleteSession, fetchMessages, fetchOverview, streamChat } from '../api/client'
import { nowClock } from '../utils/format'

defineProps({ theme: { type: String, default: 'dark' } })
defineEmits(['toggle-theme'])

const message = useMessage()

/** 服务端会话列表（来自 GET /sessions/overview） */
const sessions = ref([])
/** 本地的新会话：第一次发送后由后端创建同名 session */
const draft = ref(null)
const activeId = ref('')
const messages = ref([])

const loading = ref(false)
const sending = ref(false)
const online = ref(true)
const search = ref('')
const mobileOpen = ref(false)

const composerRef = ref(null)
const controller = ref(null)

const items = computed(() => {
  const list = sessions.value.map((item) => ({
    id: item.id,
    title: item.title || '新的对话',
    messageCount: item.message_count,
    updatedAt: item.updated_at,
  }))
  if (draft.value) {
    list.unshift({
      id: draft.value.id,
      title: draft.value.title,
      messageCount: messages.value.filter((item) => item.role === 'user').length,
      updatedAt: draft.value.updatedAt,
    })
  }
  return list
})

const filtered = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return items.value
  return items.value.filter((item) => item.title.toLowerCase().includes(keyword))
})

const activeTitle = computed(
  () => items.value.find((item) => item.id === activeId.value)?.title || '新的对话',
)

const subtitle = computed(() => {
  const first = messages.value.find((item) => item.role === 'user')
  return first ? first.content.slice(0, 40) : '与 DeepSeek 实时对话'
})

async function loadSessions() {
  const data = await fetchOverview()
  sessions.value = data.sessions || []
  online.value = true
  if (draft.value && sessions.value.some((item) => item.id === draft.value.id)) {
    draft.value = null
  }
}

async function loadMessages(id) {
  loading.value = true
  try {
    const data = await fetchMessages(id)
    messages.value = (data.messages || []).map((item) => ({
      role: item.role,
      content: item.content,
    }))
    online.value = true
  } catch (error) {
    if (error.status === 404) {
      messages.value = []
      return
    }
    online.value = false
    message.error('加载消息失败：' + error.message)
  } finally {
    loading.value = false
  }
}

function newChat() {
  const id = 'web-' + Math.random().toString(36).slice(2, 8)
  draft.value = { id, title: '新的对话', updatedAt: new Date().toISOString() }
  activeId.value = id
  messages.value = []
  loading.value = false
  search.value = ''
  mobileOpen.value = false
  nextTick(() => composerRef.value?.focus())
}

async function select(id) {
  mobileOpen.value = false
  if (id === activeId.value) return
  activeId.value = id
  if (draft.value && draft.value.id === id) {
    messages.value = []
    return
  }
  await loadMessages(id)
}

async function retry() {
  try {
    await loadSessions()
    if (activeId.value && !(draft.value && draft.value.id === activeId.value)) {
      await loadMessages(activeId.value)
    } else if (!activeId.value) {
      if (sessions.value.length) await select(sessions.value[0].id)
      else newChat()
    }
    message.success('已重新连接后端')
  } catch (error) {
    message.error('仍然连不上后端：' + error.message)
  }
}

async function send(text) {
  const content = String(text || '').trim()
  if (!content || sending.value) return

  messages.value.push({ role: 'user', content, time: nowClock() })
  const assistant = reactive({ role: 'assistant', content: '', time: '', streaming: true })
  messages.value.push(assistant)

  sending.value = true
  const abort = new AbortController()
  controller.value = abort

  try {
    await streamChat({
      sessionId: activeId.value,
      message: content,
      signal: abort.signal,
      onDelta: (_chunk, answer) => {
        assistant.content = answer
      },
    })
    assistant.streaming = false
    assistant.time = nowClock()
    online.value = true
    await loadSessions()
  } catch (error) {
    assistant.streaming = false
    if (error.name === 'AbortError') {
      assistant.time = nowClock()
      if (!assistant.content) messages.value.pop()
      loadSessions().catch(() => {})
      return
    }
    // 后端整轮事务已回滚：本地也把这一轮撤掉，并把输入还给用户
    if (!assistant.content) {
      messages.value.splice(messages.value.length - 2, 2)
      composerRef.value?.fill(content)
    } else {
      assistant.content += '\n\n（连接中断，回复可能不完整）'
    }
    online.value = false
    message.error('发送失败：' + error.message)
  } finally {
    sending.value = false
    controller.value = null
  }
}

function stop() {
  controller.value?.abort()
}

async function removeSession(id) {
  if (!id) return
  try {
    await deleteSession(id)
    if (draft.value && draft.value.id === id) draft.value = null
    await loadSessions()
    if (activeId.value === id) {
      if (sessions.value.length) await select(sessions.value[0].id)
      else newChat()
    }
    message.success('会话已删除')
  } catch (error) {
    message.error('删除失败：' + error.message)
  }
}

function pickSuggestion(text) {
  composerRef.value?.fill(text)
}

onMounted(async () => {
  try {
    await loadSessions()
    if (sessions.value.length) await select(sessions.value[0].id)
    else newChat()
  } catch (error) {
    online.value = false
    newChat()
    message.error('后端未连接：' + error.message)
  }
})

onBeforeUnmount(() => {
  controller.value?.abort()
})
</script>

<template>
  <div class="app-shell">
    <AppSidebar
      :conversations="filtered"
      :active-id="activeId"
      :search="search"
      :theme="theme"
      :open="mobileOpen"
      :online="online"
      @update:search="search = $event"
      @select="select"
      @new="newChat"
      @remove="removeSession"
      @toggle-theme="$emit('toggle-theme')"
      @close="mobileOpen = false"
    />

    <transition name="fade">
      <div v-if="mobileOpen" class="backdrop" @click="mobileOpen = false" />
    </transition>

    <main class="main">
      <ChatHeader
        :title="activeTitle"
        :subtitle="subtitle"
        :count="messages.length"
        @menu="mobileOpen = true"
        @clear="removeSession(activeId)"
      />

      <div v-if="!online" class="offline-bar">
        <span>后端未连接（127.0.0.1:8000），检查服务是否已启动</span>
        <button @click="retry">重试</button>
      </div>

      <section class="messages-wrap">
        <MessageList :messages="messages" :loading="loading" @pick="pickSuggestion" />
      </section>

      <footer class="composer-wrap">
        <ChatComposer
          ref="composerRef"
          :sending="sending"
          @send="send"
          @stop="stop"
        />
        <p class="composer-note">对话会保存到 SQLite，刷新或重启服务后仍然在</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr);
  height: 100vh;
  overflow: hidden;
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
}

.offline-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 24px;
  font-size: 11.5px;
  color: #ffb4b4;
  background: rgba(240, 97, 109, 0.12);
  border-bottom: 1px solid rgba(240, 97, 109, 0.28);
}

.offline-bar button {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 180, 180, 0.4);
  color: #ffd7d7;
  font-size: 11px;
}

.offline-bar button:hover {
  background: rgba(240, 97, 109, 0.2);
}

.messages-wrap {
  flex: 1;
  min-height: 0;
}

.composer-wrap {
  padding: 0 24px 16px;
}

.composer-note {
  margin-top: 10px;
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
}

.backdrop {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .composer-wrap {
    padding: 0 14px 12px;
  }
  .offline-bar {
    padding: 8px 14px;
  }
}
</style>
