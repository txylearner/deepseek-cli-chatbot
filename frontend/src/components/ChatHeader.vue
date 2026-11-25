<script setup>
import { NPopconfirm, NTag } from 'naive-ui'
import { Menu, Sparkles, Trash2 } from 'lucide-vue-next'

defineProps({
  title: { type: String, default: '对话' },
  subtitle: { type: String, default: '' },
  count: { type: Number, default: 0 },
})
defineEmits(['menu', 'clear'])
</script>

<template>
  <header class="header">
    <button class="icon-btn menu-btn" aria-label="打开会话列表" @click="$emit('menu')">
      <Menu :size="18" />
    </button>

    <div class="title-block">
      <h1>{{ title }}</h1>
      <p>{{ subtitle || '与 DeepSeek 实时对话' }}</p>
    </div>

    <n-tag class="model-tag" size="small" round :bordered="false">
      <Sparkles :size="12" class="tag-icon" />
      deepseek-chat
    </n-tag>

    <span v-if="count" class="count">{{ count }} 条消息</span>

    <div class="actions">
      <n-popconfirm @positive-click="$emit('clear')">
        <template #trigger>
          <button class="icon-btn" aria-label="删除当前会话">
            <Trash2 :size="16" />
          </button>
        </template>
        删除当前会话？聊天记录会一起删除
      </n-popconfirm>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 72px;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), transparent);
}

.menu-btn {
  display: none;
}

.title-block {
  min-width: 0;
  line-height: 1.35;
}

.title-block h1 {
  font-size: 15px;
  font-weight: 650;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.title-block p {
  font-size: 11.5px;
  color: var(--text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-2);
  background: var(--panel-2);
  font-size: 10.5px;
}

.tag-icon {
  color: var(--accent);
}

.count {
  font-size: 10.5px;
  color: var(--text-3);
}

.actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

@media (max-width: 960px) {
  .header {
    padding: 0 14px;
  }
  .menu-btn {
    display: grid;
  }
  .model-tag,
  .count {
    display: none;
  }
}
</style>
