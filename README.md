# DeepSeek 对话机器人（前后端两目录）

第 2～5 次作业把这个项目从命令行聊天做到 FastAPI + SQLite + SQLAlchemy ORM 的 Web 服务；
第 6 次只做工程整理，把仓库拆成清晰的前后端两目录：

- `backend/`：聊天机器人后端（FastAPI + SQLAlchemy + SQLite + 测试），以及原来的聊天页源码 `webui/` 与构建脚本
- `frontend/`：Vue 3 + Vite + Naive UI 的**聊天界面**，含会话栏、消息气泡、代码块、空状态与深浅主题

> 前端已通过 Vite 代理接上后端：**先启动 `backend/`（8000），再启动 `frontend/`（5173）**，
> 会话列表、历史消息、流式对话、删除会话都是真实数据，接口说明见 [frontend/README.md](frontend/README.md)。

## 一键启动（推荐）

在仓库根目录执行一条命令，后端和前端一起起来：

~~~powershell
.\start.ps1
~~~

脚本会依次启动 uvicorn（8000）与 vite（5173），等两者就绪后自动打开浏览器；
按 `Ctrl+C` 同时停止两个服务。不想自动开浏览器就加 `-NoBrowser`：

~~~powershell
.\start.ps1 -NoBrowser
~~~

> 首次使用前仍需各装一次依赖：`cd backend; pip install -e ".[dev]"`、`cd frontend; npm install`。

## 目录结构

~~~text
.
├── backend/                 # 后端（必须在 backend/ 目录下执行命令）
│   ├── src/chatbot/         # FastAPI 应用（api / services / repositories / db / llm）
│   ├── webui/               # 聊天页源码，构建成 src/chatbot/static/index.html
│   ├── scripts/             # build_frontend.py：内联 + 压缩页面
│   ├── tests/               # 51 个离线测试
│   ├── pyproject.toml
│   └── README.md            # 后端的详细说明
├── frontend/                # Vue 3 + Vite + Naive UI 聊天界面
│   ├── src/api/client.js    # 调后端 /sessions、/chat/stream
│   ├── src/components/      # 侧边栏、消息列表、气泡、输入框、空状态
│   └── index.html
├── .gitignore
└── README.md                # 本文件
~~~

## 后端：安装、启动、测试

**所有命令都在 `backend/` 目录下执行**（`.env`、`chat.db`、`src/chatbot/static/` 都按工作目录或包目录解析）。

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

# 第一次运行：从模板复制配置并填入 DeepSeek API Key
Copy-Item .env.example .env
~~~

启动服务（8000 端口）：

~~~powershell
python -m uvicorn chatbot.app:app --reload --port 8000
~~~

- 聊天页面：<http://127.0.0.1:8000/>
- 接口文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

跑测试（离线，假模型客户端 + 临时 SQLite，不需要真实 Key）：

~~~powershell
python -m pytest -q
~~~

数据库结构、接口清单、事务设计与聊天页构建方式见 [backend/README.md](backend/README.md)。

## 前端：安装与启动

**先确保后端在 8000 端口运行**（见上一节），再开一个终端：

~~~powershell
cd frontend
npm install
npm run dev
~~~

浏览器打开 <http://localhost:5173/>，就是完整的聊天界面：

- 左侧会话栏：后端返回的真实会话，可新建、搜索、切换、删除，底部切换深浅主题
- 中间对话区：用户/助手气泡、代码块与复制、流式输出、加载骨架屏、空状态
- 底部输入区：Enter 发送、Shift+Enter 换行，生成中按钮变成「停止」
- 顶部：会话标题、`deepseek-chat` 标签、消息数、删除会话（带确认）

开发服务器通过 `vite.config.js` 的代理把 `/chat`、`/sessions`、`/health` 转发到 `127.0.0.1:8000`，
所以页面里没有跨域问题；消息写进后端 SQLite，刷新或重启服务后仍然在。
技术栈、目录与接口对照见 [frontend/README.md](frontend/README.md)。

## 仓库卫生

根 `.gitignore` 已忽略 `node_modules/`、`dist/`、`.env`、`*.db`、`__pycache__/`，这些都不进仓库。
