<script setup>
import { computed } from 'vue'
import { NInput, NScrollbar } from 'naive-ui'
import { MessageSquare, Moon, Plus, Search, Sun, Trash2, X } from 'lucide-vue-next'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
  search: { type: String, default: '' },
  theme: { type: String, default: 'dark' },
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['select', 'new', 'remove', 'update:search', 'toggle-theme', 'close'])

const keyword = computed({
  get: () => props.search,
  set: (value) => emit('update:search', value),
})

const isDark = computed(() => props.theme === 'dark')
</script>

<template>
  <aside class="sidebar" :class="{ 'is-open': open }">
    <header class="brand">
      <div class="brand-mark">
        <MessageSquare :size="17" />
      </div>
      <div class="brand-text">
        <div class="brand-name">DeepSeek 对话</div>
        <div class="brand-sub">Vue 3 · Naive UI</div>
      </div>
      <button class="icon-btn close-btn" aria-label="关闭会话列表" @click="$emit('close')">
        <X :size="16" />
      </button>
    </header>

    <button class="new-chat" @click="$emit('new')">
      <Plus :size="16" />
      <span>新建对话</span>
    </button>

    <div class="search-row">
      <n-input v-model:value="keyword" size="small" placeholder="搜索会话" clearable>
        <template #prefix>
          <Search :size="14" />
        </template>
      </n-input>
    </div>

    <n-scrollbar class="conversation-scroll">
      <div class="conversation-list">
        <button
          v-for="item in conversations"
          :key="item.id"
          class="conversation"
          :class="{ active: item.id === activeId }"
          @click="$emit('select', item.id)"
        >
          <span class="conversation-main">
            <span class="conversation-title">{{ item.title }}</span>
            <span class="conversation-meta">
              {{ item.messages.length ? item.messages.length + ' 条消息' : '暂无消息' }}
              <template v-if="item.updatedAt"> · {{ item.updatedAt }}</template>
            </span>
          </span>
          <span class="delete-btn" title="删除会话" @click.stop="$emit('remove', item.id)">
            <Trash2 :size="13" />
          </span>
        </button>

        <p v-if="!conversations.length" class="list-empty">没有匹配的会话</p>
      </div>
    </n-scrollbar>

    <footer class="sidebar-footer">
      <span class="status-dot" />
      <span class="status-text">示例数据 · 未接后端</span>
      <button class="icon-btn" :aria-label="isDark ? '切换到浅色' : '切换到深色'" @click="$emit('toggle-theme')">
        <Sun v-if="isDark" :size="16" />
        <Moon v-else :size="16" />
      </button>
    </footer>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 14px 14px;
  height: 100vh;
  border-right: 1px solid var(--border);
  background: var(--panel);
  backdrop-filter: blur(18px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 6px 0;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 8px 22px var(--accent-glow);
}

.brand-text {
  min-width: 0;
  line-height: 1.3;
}

.brand-name {
  font-size: 13.5px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.brand-sub {
  font-size: 10.5px;
  color: var(--text-3);
}

.close-btn {
  display: none;
  margin-left: auto;
}

.new-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 10px 26px var(--accent-glow);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 30px var(--accent-glow);
}
.new-chat:active {
  transform: translateY(0);
}

.search-row {
  padding: 0 2px;
}

.conversation-scroll {
  flex: 1;
  min-height: 0;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 2px;
}

.conversation {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 10px 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  text-align: left;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}
.conversation:hover {
  background: var(--panel-2);
}
.conversation.active {
  background: var(--accent-soft);
  border-color: rgba(124, 92, 255, 0.28);
}

.conversation-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.conversation-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-meta {
  font-size: 10.5px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  border-radius: 8px;
  color: var(--text-3);
  opacity: 0;
  transition: opacity 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}
.conversation:hover .delete-btn,
.conversation.active .delete-btn {
  opacity: 1;
}
.delete-btn:hover {
  background: rgba(240, 97, 109, 0.16);
  color: #f0616d;
}

.list-empty {
  padding: 26px 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-3);
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 6px 2px;
  border-top: 1px solid var(--border);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc97;
  box-shadow: 0 0 0 3px rgba(61, 220, 151, 0.16);
}

.status-text {
  flex: 1;
  font-size: 10.5px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    width: min(84vw, 320px);
    transform: translateX(-102%);
    transition: transform 0.22s ease;
    box-shadow: var(--shadow);
  }
  .sidebar.is-open {
    transform: translateX(0);
  }
  .close-btn {
    display: grid;
  }
}
</style>
