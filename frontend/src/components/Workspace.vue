<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { useMessage } from 'naive-ui'
import AppSidebar from './AppSidebar.vue'
import ChatHeader from './ChatHeader.vue'
import ChatComposer from './ChatComposer.vue'
import MessageList from './MessageList.vue'
import { demoReplies, seedConversations } from '../data/conversations'

defineProps({ theme: { type: String, default: 'dark' } })
defineEmits(['toggle-theme'])

const message = useMessage()

/** 深拷贝演示数据，避免直接改动模块级常量 */
const conversations = ref(
  seedConversations.map((item) => ({ ...item, messages: item.messages.map((m) => ({ ...m })) })),
)
const activeId = ref(conversations.value[0]?.id ?? '')
const search = ref('')
const loading = ref(false)
const sending = ref(false)
const mobileOpen = ref(false)
const composerRef = ref(null)

const active = computed(() => conversations.value.find((item) => item.id === activeId.value) ?? null)
const messages = computed(() => active.value?.messages ?? [])

const filtered = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return conversations.value
  return conversations.value.filter((item) =>
    (item.title + item.preview).toLowerCase().includes(keyword),
  )
})

let loadTimer = null
let replyTimer = null

function select(id) {
  mobileOpen.value = false
  if (id === activeId.value) return
  activeId.value = id
  loading.value = true
  clearTimeout(loadTimer)
  loadTimer = setTimeout(() => {
    loading.value = false
  }, 260)
}

function createConversation() {
  const now = Date.now()
  conversations.value.unshift({
    id: 'c' + now,
    title: '新的对话',
    preview: '',
    updatedAt: '刚刚',
    messages: [],
  })
  activeId.value = 'c' + now
  search.value = ''
  loading.value = false
  mobileOpen.value = false
  nextTick(() => composerRef.value?.focus())
}

function removeConversation(id) {
  const index = conversations.value.findIndex((item) => item.id === id)
  if (index === -1) return
  conversations.value.splice(index, 1)
  if (activeId.value === id) {
    if (conversations.value.length) {
      activeId.value = conversations.value[0].id
    } else {
      createConversation()
    }
  }
  message.success('已删除该会话（仅本地）')
}

function clearConversation() {
  if (!active.value) return
  active.value.messages = []
  active.value.preview = ''
  message.info('已清空当前对话（仅本地）')
}

function currentTime() {
  const now = new Date()
  return String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0')
}

function send(text) {
  const content = String(text || '').trim()
  if (!content || sending.value || !active.value) return

  const conversation = active.value
  conversation.messages.push({ role: 'user', content, time: currentTime() })
  if (conversation.title === '新的对话') conversation.title = content.slice(0, 18)
  conversation.preview = content.slice(0, 42)
  conversation.updatedAt = '刚刚'

  sending.value = true
  message.info('演示模式：消息还没有发送到后端')
  clearTimeout(replyTimer)
  replyTimer = setTimeout(() => {
    conversation.messages.push({
      role: 'assistant',
      content: demoReplies[Math.floor(Math.random() * demoReplies.length)],
      time: currentTime(),
    })
    sending.value = false
  }, 900)
}

function pickSuggestion(text) {
  composerRef.value?.fill(text)
}

onBeforeUnmount(() => {
  clearTimeout(loadTimer)
  clearTimeout(replyTimer)
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
      @update:search="search = $event"
      @select="select"
      @new="createConversation"
      @remove="removeConversation"
      @toggle-theme="$emit('toggle-theme')"
      @close="mobileOpen = false"
    />

    <transition name="fade">
      <div v-if="mobileOpen" class="backdrop" @click="mobileOpen = false" />
    </transition>

    <main class="main">
      <ChatHeader
        :title="active ? active.title : '对话'"
        :subtitle="active && active.messages.length ? active.preview : '与 DeepSeek 实时对话'"
        :count="active ? active.messages.length : 0"
        @menu="mobileOpen = true"
        @clear="clearConversation"
      />

      <section class="messages-wrap">
        <MessageList
          :messages="messages"
          :loading="loading"
          :sending="sending"
          @pick="pickSuggestion"
        />
      </section>

      <footer class="composer-wrap">
        <ChatComposer ref="composerRef" :disabled="sending || !active" @send="send" />
        <p class="composer-note">前端演示界面 · 尚未接入 /chat 接口</p>
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
}
</style>
