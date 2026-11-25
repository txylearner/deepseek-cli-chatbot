# frontend —— 聊天界面

Vue 3 + Vite 的聊天前端，**已经接上 backend 的接口**：会话列表、历史消息、流式对话、删除会话都是真实数据，
消息写进后端的 SQLite。

## 前置条件

先把后端跑起来（8000 端口）：

~~~powershell
cd ../backend
.\.venv\Scripts\python.exe -m uvicorn chatbot.app:app --host 127.0.0.1 --port 8000
~~~

开发服务器通过 Vite 代理把 `/chat`、`/sessions`、`/health` 转发到 `http://127.0.0.1:8000`（见 `vite.config.js`），
所以前端代码里只写相对路径，同源部署时不用改。

## 命令

~~~bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # 产物在 dist/（已忽略）
npm run preview
~~~

## 技术栈

| 用途 | 选型 |
|---|---|
| 框架 | Vue 3（`<script setup>` + 组合式 API） |
| 构建 | Vite 8 |
| 组件库 | [Naive UI](https://www.naiveui.com/) |
| 图标 | [Lucide](https://lucide.dev/) |
| 样式 | 原生 CSS 变量 + scoped 样式 |

## 目录

~~~text
src/
├── App.vue                 # 主题状态 + ConfigProvider / MessageProvider
├── main.js
├── theme.js                # Naive UI 主题变量（亮/暗）
├── assets/main.css         # 设计变量与全局样式
├── api/client.js           # 后端接口：overview / messages / delete / stream
├── utils/format.js         # “刚刚 / 今天 10:24 / 昨天” 时间格式
└── components/
    ├── Workspace.vue       # 容器：会话状态、流式发送、删除、离线重试
    ├── AppSidebar.vue      # 侧边栏：会话列表、搜索、新建、主题
    ├── ChatHeader.vue      # 顶部：标题、模型标签、删除确认
    ├── MessageList.vue     # 消息区：骨架屏 / 空状态 / 气泡
    ├── MessageBubble.vue   # 气泡：代码块、复制、流式光标
    ├── EmptyState.vue      # 空状态与示例话题
    └── ChatComposer.vue    # 输入区：Enter 发送、停止生成
~~~

## 对接的接口

| 前端动作 | 后端接口 |
|---|---|
| 启动 / 新建后刷新会话 | `GET /sessions/overview` |
| 点开某个会话 | `GET /sessions/{id}/messages` |
| 发送消息 | `POST /chat/stream`（逐块读取纯文本，边读边渲染） |
| 删除会话 | `DELETE /sessions/{id}` |
| 侧边栏连接状态 | 请求成功即视为在线，失败切到“后端未连接” |

新建对话时前端先用 `web-xxxx` 作临时会话 ID，第一次发送由后端 `append_turn()` 创建会话并落库，
流结束后再拉一次 `/sessions/overview` 刷新标题和排序。

## 界面状态

- **加载**：切换会话时显示骨架屏
- **空**：新会话显示引导页与示例话题
- **离线**：顶部出现红色提示条，可点「重试」；侧边栏状态点变红
- **发送失败**：后端整轮回滚，前端撤掉这一轮气泡并把输入还给用户
- **停止生成**：发送中按钮变成停止，`AbortController` 中断流；已生成的部分仍会由后端落库

## UI 组件与素材来源

- Naive UI —— <https://www.naiveui.com/>
- Lucide —— <https://lucide.dev/>

同类可替换资源：Uiverse、shadcn-vue、daisyUI、Element Plus、Arco Design Vue、PrimeVue、Vuetify、
HyperUI / Flowbite（详见项目根 README 的选择说明）。
