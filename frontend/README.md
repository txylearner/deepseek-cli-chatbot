# frontend —— 聊天界面

仓库的前端：Vue 3 + Vite 的聊天界面外壳，`npm run dev` 打开就能看到完整布局与交互。

> 目前用的是**本地演示数据**（`src/data/conversations.js`），还没有接后端接口；
> 消息、会话都只存在浏览器内存里，刷新即恢复示例数据。

## 技术栈

| 用途 | 选型 |
|---|---|
| 框架 | Vue 3（`<script setup>` + 组合式 API） |
| 构建 | Vite 8 |
| 组件库 | [Naive UI](https://www.naiveui.com/)（按钮、输入框、标签、滚动条、骨架屏、消息提示） |
| 图标 | [Lucide](https://lucide.dev/)（`lucide-vue-next`） |
| 样式 | 原生 CSS 变量 + 组件内 scoped 样式，不依赖 Tailwind |

## 命令

~~~bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # 产物在 dist/（已忽略，不进仓库）
npm run preview
~~~

## 目录

~~~text
src/
├── App.vue                 # 主题状态 + Naive UI 的 ConfigProvider / MessageProvider
├── main.js                 # 入口
├── theme.js                # Naive UI 主题变量（亮/暗两套共用一个品牌色）
├── assets/main.css         # 设计变量、重置、滚动条、通用样式
├── data/conversations.js   # 演示会话与消息（形状对齐后端 messages 响应）
└── components/
    ├── Workspace.vue       # 容器：会话状态、发送、选中、删除
    ├── AppSidebar.vue      # 侧边栏：品牌、新建、搜索、会话列表、主题开关
    ├── ChatHeader.vue      # 顶部：标题、模型标签、消息数、清空
    ├── MessageList.vue     # 消息区：骨架屏 / 空状态 / 气泡列表 / 输入中动画
    ├── MessageBubble.vue   # 单条消息：气泡、代码块、复制
    ├── EmptyState.vue      # 空状态：引导语 + 四个示例话题
    └── ChatComposer.vue    # 输入区：自适应高度、Enter 发送、字数
~~~

## 界面能力

- **布局**：左侧会话栏 + 右侧对话区，宽度 ≤960px 时侧边栏收成抽屉（顶部菜单按钮打开）
- **主题**：深色 / 浅色两套，`localStorage` 记忆；调试时可用 `?theme=light`、`?theme=dark` 强制指定
- **会话**：新建、切换、按标题/摘要搜索、删除（悬停出现删除按钮）
- **消息**：用户气泡靠右、助手气泡靠左；代码块带语言标签与「复制」；支持滚动查看
- **三态**：切换会话时显示骨架屏（加载态）、没有消息时显示空状态；错误态等接上接口后再补
- **输入**：自适应高度、Enter 发送 / Shift+Enter 换行、字数统计、生成中禁用

## UI 组件与素材来源

实际用到的是这两个：

- **Naive UI** —— 组件与主题变量：<https://www.naiveui.com/>（[组件总览](https://www.naiveui.com/en-US/os-theme/components/button)）
- **Lucide** —— 图标：<https://lucide.dev/>

同类的开源资源（想换风格时可以直接替换）：

| 站点 | 提供什么 | 适合谁 |
|---|---|---|
| [Uiverse](https://uiverse.io/) | 社区投稿的按钮、开关、卡片、加载动画，纯 CSS/HTML 片段 | 想单独抄一个「按钮」的样式 |
| [shadcn-vue](https://www.shadcn-vue.com/) | 基于 Tailwind + Reka UI 的复制粘贴式组件 | 想完全掌控样式、不想被组件库绑住 |
| [daisyUI](https://daisyui.com/) | Tailwind 的语义类名（`btn`、`card`、`badge`） | 已用 Tailwind，想少写样式 |
| [Element Plus](https://element-plus.org/) | Vue 3 组件库，中文文档最全 | 后台管理类项目 |
| [Arco Design Vue](https://arco.design/vue) | 字节系设计语言，视觉统一 | 想要现成的企业级观感 |
| [PrimeVue](https://primevue.org/) | 组件全、主题多 | 需要复杂表格/表单 |
| [Vuetify](https://vuetifyjs.com/) | Material Design 规范 | 想要 Material 风格 |
| [HyperUI](https://www.hyperui.dev/) / [Flowbite](https://flowbite.com/) | Tailwind 的整块页面片段（导航、卡片、表单） | 想快速拼页面 |

## 接后端时改哪里

接口契约见 [`../backend/README.md`](../backend/README.md)，改三个地方即可：

1. `src/data/conversations.js` → 换成 `GET /sessions/overview` 与会话消息接口（`GET /sessions/{id}/messages?keyword=`）
2. `Workspace.vue` 的 `send()` → 调 `POST /chat/stream`，把返回的文本块累加进气泡（流式渲染）
3. `AppSidebar.vue` 的删除 → 调 `DELETE /sessions/{id}`

接口没通之前，界面显示的「示例数据 · 未接后端」就是提醒。
