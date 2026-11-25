<script setup>
import { nextTick, ref, watch } from 'vue'
import { NSkeleton } from 'naive-ui'
import MessageBubble from './MessageBubble.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  sending: { type: Boolean, default: false },
})
defineEmits(['pick'])

const scroller = ref(null)

function scrollToBottom() {
  nextTick(() => {
    const el = scroller.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(
  () => props.loading,
  (value) => {
    if (!value) scrollToBottom()
  },
)
</script>

<template>
  <div ref="scroller" class="messages">
    <div class="inner">
      <template v-if="loading">
        <div v-for="row in 3" :key="row" class="skeleton-row" :class="{ right: row === 2 }">
          <n-skeleton circle :width="34" :height="34" />
          <n-skeleton text :width="row === 2 ? '42%' : '68%'" :height="row === 2 ? 44 : 76" />
        </div>
      </template>

      <EmptyState v-else-if="!messages.length" @pick="$emit('pick', $event)" />

      <template v-else>
        <MessageBubble v-for="(item, index) in messages" :key="index" :message="item" />
        <div v-if="sending" class="typing">
          <span /><span /><span />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.messages {
  height: 100%;
  overflow-y: auto;
  padding: 28px 24px 8px;
}

.inner {
  max-width: 900px;
  margin: 0 auto;
}

.skeleton-row {
  display: flex;
  gap: 12px;
  width: min(860px, 100%);
  margin: 0 auto 22px;
}

.skeleton-row.right {
  flex-direction: row-reverse;
}

.typing {
  display: flex;
  gap: 5px;
  width: min(860px, 100%);
  margin: 0 auto 22px;
  padding-left: 46px;
}

.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-3);
  animation: blink 1.2s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 80%, 100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

@media (max-width: 640px) {
  .messages {
    padding: 18px 14px 4px;
  }
}
</style>
