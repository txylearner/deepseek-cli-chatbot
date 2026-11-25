# DeepSeek 对话机器人（前后端两目录）

第 2～5 次作业把这个项目从命令行聊天做到 FastAPI + SQLite + SQLAlchemy ORM 的 Web 服务；
第 6 次只做工程整理，把仓库拆成清晰的前后端两目录：

- `backend/`：聊天机器人后端（FastAPI + SQLAlchemy + SQLite + 测试），以及原来的聊天页源码 `webui/` 与构建脚本
- `frontend/`：用 `npm create vue@latest` 生成的**空 Vue 3 + Vite 工程**

> 本次前端只是脚手架，尚未接入 API：没有写 Vue 组件、没有调用 `/chat`、也没有前后端联调。

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
├── frontend/                # Vue 3 + Vite 空工程
│   ├── src/
│   ├── index.html
│   └── package.json
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

浏览器打开 <http://localhost:5173/>，能看到 Vue 的默认欢迎页。
本次只验证脚手架能跑起来，没有任何业务代码。

## 仓库卫生

根 `.gitignore` 已忽略 `node_modules/`、`dist/`、`.env`、`*.db`、`__pycache__/`，这些都不进仓库。
