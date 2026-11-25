<script setup>
import { nextTick, ref, watch } from 'vue'
import { NSkeleton } from 'naive-ui'
import MessageBubble from './MessageBubble.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
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

@media (max-width: 640px) {
  .messages {
    padding: 18px 14px 4px;
  }
}
</style>
