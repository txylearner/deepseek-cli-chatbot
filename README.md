# DeepSeek 对话机器人（FastAPI + SQLite）

第 2 次作业是命令行聊天机器人，第 3 次把它改造成 HTTP 服务，第 4 次继续改造：
会话从内存搬进 SQLite，后端按分层架构拆分，前端源码与构建产物分离。

## 本次改造点

| 作业要求 | 实现位置 |
|---|---|
| 会话存入 SQLite | `src/chatbot/db/schema.py`、`repositories/session_repository.py` |
| README 用 mermaid 画 ER 图 | 本文“数据库”一节，与建表语句逐字对应 |
| 纯 HTML 前端，8000 端口托管 | `frontend/` 源码 → 构建成 `src/chatbot/static/index.html` |
| 数据库读写集中在存储模块 | `repositories/`，路由与 Service 里没有 SQL |
| 自动建表、`*.db` 不提交 | 仓库初始化建表；`.gitignore` 忽略 `*.db` |
| 离线测试 | `tests/` 共 31 个用例，假模型 + 临时数据库 |

## 功能

- `POST /chat` 一问一答，按 `session_id` 维护多轮历史
- `POST /chat/stream` 流式输出（`StreamingResponse` 逐块返回）
- `GET /sessions`、`GET /sessions/overview`、`GET /sessions/{id}/messages`、`DELETE /sessions/{id}`
- `POST /study/word` 学习功能：英语单词讲解
- 会话与消息写入 SQLite，服务重启后历史仍在
- 网页聊天界面：会话列表（消息数 + 最近时间）、历史消息、新建 / 切换 / 清空、
  逐字输出、Markdown 渲染、深浅色主题
- 31 个离线测试

## 环境要求

- Python 3.12+
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

## 安装

~~~powershell
cd "C:\Users\谭新宇\Desktop\智能AI应用作业\第4次作业"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
~~~

配置 Key（`.env` 已被 `.gitignore` 忽略，不会提交）：

~~~powershell
Copy-Item .env.example .env
~~~

~~~dotenv
CHATBOT_API_KEY=sk-你的真实Key
~~~

## 启动服务

~~~powershell
python -m uvicorn chatbot.app:app --reload --port 8000
~~~

- 浏览器打开 <http://127.0.0.1:8000/> 就是**聊天界面**
- <http://127.0.0.1:8000/docs> 是接口文档，可以点 **Try it out** 逐个调试
- 健康检查：<http://127.0.0.1:8000/health>

首次启动会在当前目录自动创建 `chat.db` 并建表，不需要手动执行任何 SQL。

## 项目结构

~~~text
.
├── pyproject.toml
├── .env.example
├── .gitignore
├── frontend/                     # 前端源码（不直接对外托管）
│   ├── index.html                # 页面结构
│   ├── css/app.css               # 样式
│   └── js/app.js                 # 交互逻辑
├── scripts/
│   └── build_frontend.py         # 内联 + 压缩，生成 static/index.html
├── src/chatbot/
│   ├── app.py                    # 应用装配：路由、异常处理、静态托管
│   ├── __init__.py               # 版本号
│   ├── __main__.py               # python -m chatbot
│   ├── api/                      # 路由层：只做 HTTP 翻译
│   │   ├── deps.py               # 依赖注入（仓库 / 模型客户端 / Service）
│   │   ├── router.py             # 汇总各业务路由
│   │   ├── chat.py               # /chat、/chat/stream
│   │   ├── sessions.py           # /sessions 相关
│   │   ├── study.py              # /study/word
│   │   └── system.py             # /health
│   ├── services/                 # 业务层：编排顺序与失败回滚
│   │   ├── chat_service.py
│   │   └── study_service.py
│   ├── repositories/             # 仓库层：唯一读写数据的地方
│   │   └── session_repository.py
│   ├── db/                       # 数据库层：连接与建表
│   │   ├── connection.py
│   │   └── schema.py
│   ├── models/                   # Pydantic 请求 / 响应模型
│   │   └── schemas.py
│   ├── core/                     # 配置、提示词、领域异常
│   │   ├── config.py
│   │   ├── prompts.py
│   │   └── exceptions.py
│   ├── llm/                      # DeepSeek 调用
│   │   └── deepseek.py
│   ├── cli/                      # 命令行版（与 Web 共用 Service / Repository）
│   │   └── main.py
│   └── static/
│       └── index.html            # 前端构建产物（浏览器实际拿到的页面）
└── tests/
    ├── conftest.py               # 假模型 + 临时数据库
    ├── test_db.py                # 建表 / 历史 / 隔离 / 清空 / 重启
    ├── test_api_chat.py
    ├── test_api_sessions.py
    ├── test_api_stream.py
    ├── test_api_overview.py
    ├── test_web_ui.py
    ├── test_config.py
    └── test_llm.py
~~~

## 架构

依赖方向只有一条：`api → services → repositories → db`。

- **api**：解析请求、调用依赖、返回响应，不写业务顺序，也不写 SQL
- **services**：校验输入、决定先存后调还是先调后存、失败时回滚
- **repositories**：唯一读写会话与消息的地方，接口由 `SessionRepository` 约定
- **db**：连接参数（外键开关、超时）与建表语句

换数据库时，只需要新增一个实现 `SessionRepository` 的类，并在 `app.py` 里替换构造。

## 数据库

- 文件：默认 `chat.db`，可用环境变量 `CHATBOT_DB_PATH` 改路径
- 建表：`src/chatbot/db/schema.py` 里的 `CREATE TABLE IF NOT EXISTS`，
  仓库初始化时执行，可重复运行
- 读写：全部集中在 `repositories/session_repository.py`，路由和 Service 里没有 SQL
- 数据库文件已被 `.gitignore` 忽略，不会提交

### ER 图

下面这张图和 `db/schema.py` 的建表语句一一对应：

~~~mermaid
erDiagram
    sessions ||--o{ messages : "包含"

    sessions {
        TEXT id PK
        TEXT created_at
        TEXT updated_at
    }

    messages {
        INTEGER id PK
        TEXT session_id FK
        TEXT role
        TEXT content
        TEXT created_at
    }
~~~

### 建表语句

~~~sql
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role       TEXT    NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
~~~

- 一个会话对应零到多条消息，消息通过 `session_id` 外键指向 `sessions.id`
- 删除会话时，`ON DELETE CASCADE` 会把它的消息一起删掉
- `idx_messages_session` 让“按会话取历史”走索引，而不是全表扫描

### 验证“重启不丢数据”

~~~powershell
# 1. 发一条消息
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"我叫小明\"}"

# 2. Ctrl+C 停掉服务，再重新启动
python -m uvicorn chatbot.app:app --port 8000

# 3. 历史仍在
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages
~~~

## 前端：源码与构建产物分离

`frontend/` 里是可以阅读、修改的源码；浏览器不会直接拿到它。

~~~powershell
# 改完 frontend/ 后重新构建
python scripts/build_frontend.py

# 只检查产物是否最新（CI 用）
python scripts/build_frontend.py --check
~~~

构建脚本做三件事：

1. 把 `css/app.css` 和 `js/app.js` 内联进 `index.html`
2. 用 `rjsmin` 压缩 JavaScript，去掉注释与空白
3. 输出到 `src/chatbot/static/index.html`，由 FastAPI 托管

浏览器最终收到的是压缩后的单文件，看不到 `frontend/` 的目录结构；
`/css/app.css`、`/js/app.js` 这些源路径访问会得到 404。

需要说明的一点：**任何要在浏览器里运行的代码，最终都必须下发到客户端**，
所以“完全看不到源码”并不存在。这里的保护是三层：

- 业务逻辑、提示词、API Key 全部留在服务端，前端只是界面
- 构建时压缩、去掉注释，不保留 source map
- 页面里拦截 F12 / Ctrl+Shift+I 等快捷键，只提高随手查看的门槛

真正需要保密的东西不要放进前端。

## 接口说明

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | 一问一答，返回完整回复 |
| POST | `/chat/stream` | 一问一答，逐块返回纯文本 |
| GET | `/sessions` | 会话 ID 列表 |
| GET | `/sessions/overview` | 会话概览：标题、消息数、最近更新时间 |
| GET | `/sessions/{session_id}/messages` | 某会话的消息记录 |
| DELETE | `/sessions/{session_id}` | 清空该会话 |
| POST | `/study/word` | 学习功能：单词讲解 |
| GET | `/health` | 健康检查 |

### 1. 普通对话

~~~powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"hello\"}"
~~~

~~~json
{"session_id": "u1", "reply": "你好！有什么可以帮你？"}
~~~

同一个 `session_id` 再问一句，模型能看到之前的对话。

### 2. 会话管理

~~~powershell
curl.exe -s http://127.0.0.1:8000/sessions
curl.exe -s http://127.0.0.1:8000/sessions/overview
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages
curl.exe -s -X DELETE http://127.0.0.1:8000/sessions/u1
~~~

查询不存在的会话返回 **404**。

### 3. 流式输出

~~~powershell
curl.exe -N -X POST http://127.0.0.1:8000/chat/stream -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"tell me a joke\"}"
~~~

`-N` 关闭缓冲，可以看到文字一段段出现；流结束后完整回复写入历史。

### 4. 学习功能：单词讲解

~~~powershell
curl.exe -s -X POST http://127.0.0.1:8000/study/word -H "Content-Type: application/json" -d "{\"word\":\"apple\"}"
~~~

## 网页聊天界面

打开 <http://127.0.0.1:8000/> 即可，不需要安装前端工具，也不加载任何 CDN：

- 左侧会话列表：显示首条提问、消息数、最近更新时间；点击切换，悬停 **×** 删除
- 中间对话区：用户消息靠右，助手回复靠左逐字流出（走 `POST /chat/stream`）
- 底部输入框：**Enter 发送**、**Shift+Enter 换行**，生成中按钮变成 ■ 可停止
- 右上角 **文档** 打开接口文档，**清空** 删除当前会话，**☀️/🌙** 切换主题
- 助手回复支持 Markdown：标题、粗体、列表、行内代码、代码块、引用、链接

## 配置项

全部写在 `src/chatbot/core/config.py` 的 `Settings` 里，可被同名环境变量或 `.env` 覆盖。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CHATBOT_API_KEY` | 无（必填） | DeepSeek API Key |
| `CHATBOT_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `CHATBOT_MODEL` | `deepseek-chat` | 模型名，也可用 `deepseek-reasoner` |
| `CHATBOT_TEMPERATURE` | `0.7` | 采样温度，范围 0–2 |
| `CHATBOT_MAX_HISTORY` | `20` | 命令行版保留的最近轮数 |
| `CHATBOT_DB_PATH` | `chat.db` | SQLite 数据库文件路径 |

## 测试

~~~powershell
python -m pytest -q
~~~

31 个用例全部离线：假模型客户端 + `TestClient` + `tmp_path` 临时数据库，
不联网、不需要真实 Key，也不会碰开发者本地的 `.env` 和 `chat.db`。

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_db.py` | 建表与外键、同一会话历史连续、会话隔离、清空后消息消失、重开数据库仍在、启动自动建库 |
| `tests/test_api_chat.py` | 连续对话带上历史、会话不串、学习功能、空消息被拒、响应不含 Key |
| `tests/test_api_sessions.py` | 会话列表、消息记录、清空后 404、不存在的会话 404 |
| `tests/test_api_stream.py` | 模型收到 `stream=True`、流式内容正确、流式回复写入历史 |
| `tests/test_api_overview.py` | 概览为空、消息数与首条提问、最近会话排前面 |
| `tests/test_web_ui.py` | 首页可访问、页面已内联压缩、源码路径 404、不泄露 Key、文档未被挡 |
| `tests/test_config.py` | 配置默认值、温度越界、Key 不明文 |
| `tests/test_llm.py` | 传给模型的参数 |

## 命令行版仍可用

改造没有删掉原来的交互式聊天，它和 Web 共用同一套 Service 与 Repository：

~~~powershell
python -m chatbot
~~~

输入 `exit` 或 `quit` 退出。命令行数据同样写入 `chat.db`。

## 安全注意

- `.env` 不要提交，提交前用 `git status` 检查
- API 响应里只有 `session_id`、`reply`、`role`、`content`，不含 Key
- 数据库文件（`*.db`）已被 `.gitignore` 忽略
- 提示词、模型调用与存储逻辑全部在服务端，前端页面拿不到这些源码

## 常见问题

**`ModuleNotFoundError: No module named 'fastapi'`**

没装依赖，在项目根目录执行 `python -m pip install -e ".[dev]"`。

**`ModuleNotFoundError: No module named 'chatbot'`**

不在项目根目录，先 `cd` 到本目录。

**`[Errno 10048] address already in use`**

8000 端口被占用，换一个：`--port 8001`。

**改了 frontend/ 但页面没变**

忘记构建了，执行 `python scripts/build_frontend.py` 后刷新浏览器。

**请求返回 502**

模型调用失败（Key 错、余额不足、网络不通）。服务端只返回异常类型，不会泄露 Key。

**数据库被占用 / database is locked**

同一个 `chat.db` 被另一个进程写入；关闭另一个服务进程再试。
