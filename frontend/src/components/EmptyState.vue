<script setup>
import { Code2, Lightbulb, MessageCircle, PenLine } from 'lucide-vue-next'

defineEmits(['pick'])

const suggestions = [
  {
    icon: Code2,
    title: '写一段代码',
    desc: '用 Python 写冒泡排序',
    prompt: '用 Python 写一个冒泡排序，并逐行加注释',
  },
  {
    icon: Lightbulb,
    title: '解释概念',
    desc: 'SQLite 索引是什么',
    prompt: '解释一下 SQLite 的索引，以及为什么 LIKE 查询用不上它',
  },
  {
    icon: PenLine,
    title: '润色文字',
    desc: '把这段话改得更正式',
    prompt: '帮我把这段话改得更正式：这个方案我觉得还行，就是有点慢',
  },
  {
    icon: MessageCircle,
    title: '随便聊聊',
    desc: '讲个笑话',
    prompt: '讲个程序员笑话',
  },
]
</script>

<template>
  <div class="empty">
    <div class="orb">
      <div class="orb-core" />
    </div>

    <h2>开始一段新对话</h2>
    <p class="sub">界面已经就绪，接上 /chat 就能聊起来；先选一个话题试试布局。</p>

    <div class="suggestions">
      <button
        v-for="item in suggestions"
        :key="item.title"
        class="suggestion"
        @click="$emit('pick', item.prompt)"
      >
        <span class="icon-wrap">
          <component :is="item.icon" :size="16" />
        </span>
        <span class="text">
          <span class="title">{{ item.title }}</span>
          <span class="desc">{{ item.desc }}</span>
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 40px 8px 20px;
  text-align: center;
}

.orb {
  position: relative;
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  margin-bottom: 22px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, var(--accent-soft), transparent 60%);
}

.orb::before,
.orb::after {
  content: "";
  position: absolute;
  inset: 6px;
  border-radius: 50%;
  border: 1px solid var(--border-strong);
}

.orb::after {
  inset: 18px;
  border-style: dashed;
  opacity: 0.6;
  animation: spin 18s linear infinite;
}

.orb-core {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 0 28px var(--accent-glow);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

h2 {
  font-size: 19px;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.sub {
  margin-top: 8px;
  max-width: 460px;
  font-size: 12.5px;
  color: var(--text-2);
  line-height: 1.7;
}

.suggestions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: min(560px, 100%);
  margin-top: 26px;
}

.suggestion {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 13px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--ai-bubble);
  text-align: left;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.suggestion:hover {
  transform: translateY(-2px);
  border-color: rgba(124, 92, 255, 0.45);
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.18);
}

.icon-wrap {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 9px;
  color: var(--accent);
  background: var(--accent-soft);
}

.text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.desc {
  font-size: 11px;
  color: var(--text-2);
}

@media (max-width: 640px) {
  .suggestions {
    grid-template-columns: minmax(0, 1fr);
  }
  .empty {
    padding-top: 24px;
  }
}
</style>
