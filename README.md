# DeepSeek 对话机器人（前后端两目录）

第 2～5 次作业把这个项目从命令行聊天做到 FastAPI + SQLite + SQLAlchemy ORM 的 Web 服务；
第 6 次只做工程整理，把仓库拆成清晰的前后端两目录：

- `backend/`：聊天机器人后端（FastAPI + SQLAlchemy + SQLite + 测试），以及原来的聊天页源码 `webui/` 与构建脚本
- `frontend/`：Vue 3 + Vite + Naive UI 的**聊天界面**，含会话栏、消息气泡、代码块、空状态与深浅主题

> 前端目前用本地演示数据（`src/data/conversations.js`），还没有接 `/chat` 接口；
> 界面与交互可以单独跑，接入位置见 [frontend/README.md](frontend/README.md)。

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
│   ├── src/components/      # 侧边栏、消息列表、气泡、输入框、空状态
│   ├── src/data/            # 本地演示数据（接后端前的占位）
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

~~~powershell
cd frontend
npm install
npm run dev
~~~

浏览器打开 <http://localhost:5173/>，可以看到聊天界面：

- 左侧会话栏：新建、搜索、切换、删除会话，底部切换深浅主题
- 中间对话区：用户/助手气泡、代码块与复制、加载骨架屏、空状态
- 底部输入区：Enter 发送、Shift+Enter 换行，生成中禁用

界面用的是 Naive UI 组件 + Lucide 图标 + 自定义 CSS 变量，技术栈、目录与组件来源见
[frontend/README.md](frontend/README.md)。数据目前是演示数据，刷新即恢复示例会话。

## 仓库卫生

根 `.gitignore` 已忽略 `node_modules/`、`dist/`、`.env`、`*.db`、`__pycache__/`，这些都不进仓库。
