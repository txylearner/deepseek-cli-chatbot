<script setup>
import { computed, ref } from 'vue'
import { NInput } from 'naive-ui'
import { Send, Square } from 'lucide-vue-next'

const props = defineProps({
  sending: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'stop'])

const value = ref('')
const inputRef = ref(null)
const canSend = computed(() => value.value.trim().length > 0 && !props.sending)

function submit() {
  const text = value.value.trim()
  if (!text || props.sending) return
  emit('send', text)
  value.value = ''
}

function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}

defineExpose({
  focus: () => inputRef.value?.focus(),
  fill: (text) => {
    value.value = text
    inputRef.value?.focus()
  },
})
</script>

<template>
  <div class="composer" :class="{ muted: sending }" @keydown="onKeydown">
    <n-input
      ref="inputRef"
      v-model:value="value"
      type="textarea"
      :bordered="false"
      :autosize="{ minRows: 1, maxRows: 6 }"
      placeholder="给 DeepSeek 发消息…"
    />

    <div class="bar">
      <span class="hint">
        <kbd>Enter</kbd> 发送 · <kbd>Shift</kbd> + <kbd>Enter</kbd> 换行
      </span>
      <div class="right">
        <span v-if="value.length" class="count">{{ value.length }}</span>
        <button
          v-if="sending"
          class="send stop"
          aria-label="停止生成"
          title="停止生成"
          @click="$emit('stop')"
        >
          <Square :size="14" />
        </button>
        <button v-else class="send" :disabled="!canSend" aria-label="发送" @click="submit">
          <Send :size="17" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.composer {
  width: min(900px, 100%);
  margin: 0 auto;
  padding: 10px 12px 8px;
  border-radius: 16px;
  border: 1px solid var(--border-strong);
  background: var(--panel-solid);
  box-shadow: var(--shadow);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.composer:focus-within {
  border-color: rgba(124, 92, 255, 0.55);
  box-shadow: 0 0 0 4px rgba(124, 92, 255, 0.12), var(--shadow);
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 4px 0;
}

.hint {
  font-size: 10.5px;
  color: var(--text-3);
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count {
  font-size: 10.5px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}

.send {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 8px 20px var(--accent-glow);
  transition: transform 0.15s ease, opacity 0.15s ease, box-shadow 0.15s ease;
}

.send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px var(--accent-glow);
}

.send:disabled {
  cursor: not-allowed;
  opacity: 0.42;
  box-shadow: none;
}

.send.stop {
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--border-strong);
  box-shadow: none;
}

@media (max-width: 640px) {
  .hint {
    display: none;
  }
  .bar {
    justify-content: flex-end;
  }
}
</style>
