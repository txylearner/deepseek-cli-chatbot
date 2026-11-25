<script setup>
import { computed, ref } from 'vue'
import { Check, Copy, Sparkles } from 'lucide-vue-next'

const props = defineProps({
  message: { type: Object, required: true },
})

const copiedIndex = ref(-1)
let copyTimer = null

const isUser = computed(() => props.message.role === 'user')

const blocks = computed(() => {
  const parts = String(props.message.content || '').split('\u0060\u0060\u0060')
  const result = []
  parts.forEach((part, index) => {
    if (index % 2 === 1) {
      const lines = part.split('\n')
      const lang = (lines[0] || '').trim() || 'code'
      const code = lines.slice(1).join('\n').replace(/\n$/, '')
      result.push({ type: 'code', lang, code })
    } else if (part.trim()) {
      result.push({ type: 'text', text: part.replace(/^\n+|\n+$/g, '') })
    }
  })
  return result
})

async function copyCode(block, index) {
  try {
    await navigator.clipboard.writeText(block.code)
    copiedIndex.value = index
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => {
      copiedIndex.value = -1
    }, 1200)
  } catch {
    copiedIndex.value = -1
  }
}
</script>

<template>
  <article class="message" :class="isUser ? 'is-user' : 'is-assistant'">
    <div class="avatar" :class="isUser ? 'user-avatar' : 'ai-avatar'">
      <span v-if="isUser">你</span>
      <Sparkles v-else :size="16" />
    </div>

    <div class="body">
      <div class="meta">
        <span v-if="!isUser" class="name">DeepSeek</span>
        <span v-if="message.time" class="time">{{ message.time }}</span>
      </div>

      <div class="bubble">
        <template v-for="(block, index) in blocks" :key="index">
          <div v-if="block.type === 'code'" class="code-block">
            <div class="code-head">
              <span class="code-lang">{{ block.lang }}</span>
              <button class="code-copy" @click="copyCode(block, index)">
                <Check v-if="copiedIndex === index" :size="12" />
                <Copy v-else :size="12" />
                <span>{{ copiedIndex === index ? '已复制' : '复制' }}</span>
              </button>
            </div>
            <pre><code>{{ block.code }}</code></pre>
          </div>
          <p v-else class="text">{{ block.text }}</p>
        </template>
      </div>
    </div>
  </article>
</template>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  width: min(860px, 100%);
  margin: 0 auto 22px;
  align-items: flex-start;
}

.is-user {
  flex-direction: row-reverse;
}

.avatar {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  font-size: 11.5px;
  font-weight: 650;
  margin-top: 2px;
}

.ai-avatar {
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 8px 20px var(--accent-glow);
}

.user-avatar {
  color: var(--text);
  background: var(--panel-2);
  border: 1px solid var(--border);
}

.body {
  min-width: 0;
  max-width: min(78%, 680px);
}

.is-user .body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 10.5px;
  color: var(--text-3);
}

.name {
  font-weight: 600;
  color: var(--text-2);
}

.bubble {
  padding: 12px 15px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--ai-bubble);
  color: var(--text);
  font-size: 13.5px;
  line-height: 1.75;
  word-break: break-word;
}

.is-user .bubble {
  border-color: transparent;
  color: #fff;
  background: var(--user-bubble);
  box-shadow: 0 10px 26px var(--accent-glow);
}

.text {
  white-space: pre-wrap;
}

.text + .text {
  margin-top: 10px;
}

.code-block {
  margin: 10px 0;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.28);
  overflow: hidden;
}

html[data-theme="light"] .code-block {
  background: #0f172a;
}

.code-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 10.5px;
  color: #9aa3b8;
}

.code-lang {
  letter-spacing: 0.04em;
  text-transform: lowercase;
}

.code-copy {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  color: #9aa3b8;
  background: transparent;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.code-copy:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e8ecf7;
}

.code-block pre {
  margin: 0;
  padding: 12px 14px;
  overflow-x: auto;
}

.code-block code {
  font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
  font-size: 12px;
  line-height: 1.7;
  color: #dbe4ff;
}

.is-user .bubble :deep(.code-block) {
  background: rgba(0, 0, 0, 0.22);
}

@media (max-width: 640px) {
  .body {
    max-width: 86%;
  }
  .bubble {
    font-size: 13px;
  }
}
</style>
