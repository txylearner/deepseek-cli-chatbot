# DeepSeek 对话机器人（FastAPI + SQLite）

第 2 次作业是命令行聊天机器人，第 3 次把它改造成 HTTP 服务，这一次继续改造：

- **分层架构**：路由（api）→ 业务（services）→ 仓库（repositories）→ 数据库（db），
  每一层只依赖下一层，换存储时路由和业务不用动；
- **SQLite 持久化**：会话和消息从内存搬到 `chat.db`，服务重启后历史还在；
- **纯 HTML 前端**：一个页面就能聊天，由后端在 8000 端口托管，不依赖任何 CDN 框架；
- **完全离线测试**：假模型 + 临时数据库，不联网、不需要真实 Key。

## 功能

- `POST /chat` 一问一答，按 `session_id` 维护多轮历史
- `POST /chat/stream` 流式输出（`StreamingResponse` 逐块返回）
- `GET /sessions`、`GET /sessions/{id}/messages`、`DELETE /sessions/{id}` 会话管理
- `POST /study/word` 学习功能：英语单词讲解
- 会话与消息写入 SQLite，启动时自动建表
- 网页聊天界面：会话列表、历史消息、新建 / 切换 / 清空、逐字输出、Markdown 渲染
- 25 个离线测试

## 环境要求

- Python 3.12+
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

## 安装

~~~powershell
cd "第4次作业"
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
├── src/chatbot/
│   ├── app.py                   # 应用装配：注册路由、异常处理、静态托管
│   ├── __init__.py              # 版本号
│   ├── __main__.py              # python -m chatbot
│   ├── api/                     # 路由层：只做 HTTP 翻译
│   │   ├── deps.py              # 依赖注入（仓库 / 模型客户端 / Service）
│   │   ├── router.py            # 汇总各业务路由
│   │   ├── chat.py              # /chat、/chat/stream
│   │   ├── sessions.py          # /sessions 相关
│   │   ├── study.py             # /study/word
│   │   └── system.py            # /health
│   ├── services/                # 业务层：编排顺序与失败回滚
│   │   ├── chat_service.py
│   │   └── study_service.py
│   ├── repositories/            # 仓库层：唯一读写数据的地方
│   │   └── session_repository.py
│   ├── db/                      # 数据库层：连接与建表
│   │   ├── connection.py
│   │   └── schema.py
│   ├── models/                  # Pydantic 请求 / 响应模型
│   │   └── schemas.py
│   ├── core/                    # 配置、提示词、领域异常
│   │   ├── config.py
│   │   ├── prompts.py
│   │   └── exceptions.py
│   ├── llm/                     # DeepSeek 调用
│   │   └── deepseek.py
│   ├── cli/                     # 命令行版（与 Web 共用 Service / Repository）
│   │   └── main.py
│   └── static/
│       └── index.html           # 前端构建产物（浏览器实际拿到的页面）
└── tests/
    ├── conftest.py              # 假模型 + 临时数据库
    ├── test_db.py               # 建表 / 历史 / 隔离 / 清空 / 重启
    ├── test_api_chat.py
    ├── test_api_sessions.py
    ├── test_api_stream.py
    ├── test_web_ui.py
    ├── test_config.py
    └── test_llm.py
~~~

## 数据库

- 文件：默认 `chat.db`，可用环境变量 `CHATBOT_DB_PATH` 改路径
- 建表：`src/chatbot/db/schema.py` 里的 `CREATE TABLE IF NOT EXISTS`，
  仓库初始化时执行，可重复运行
- 结构：`sessions`（会话）与 `messages`（消息），消息通过外键指向会话；
  删除会话时消息级联删除
- 读写：全部集中在 `repositories/session_repository.py`，路由和 Service 里没有 SQL
- 数据库文件已被 `.gitignore` 忽略，不会提交

验证“重启不丢数据”：

~~~powershell
# 1. 发一条消息
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"我叫小明\"}"

# 2. Ctrl+C 停掉服务，再重新启动
python -m uvicorn chatbot.app:app --port 8000

# 3. 历史仍在
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages
~~~

## 接口说明

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | 一问一答，返回完整回复 |
| POST | `/chat/stream` | 一问一答，逐块返回纯文本 |
| GET | `/sessions` | 会话 ID 列表 |
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

- 左侧会话列表：**＋ 新对话**、点击切换、悬停出现 **×** 删除
- 中间对话区：用户消息靠右，助手回复靠左逐字流出（走 `POST /chat/stream`）
- 底部输入框：**Enter 发送**、**Shift+Enter 换行**，生成中按钮变成 ■ 可停止
- 右上角 **清空** 删除当前会话，**☀️/🌙** 切换主题
- 助手回复支持 Markdown：标题、粗体、列表、行内代码、代码块、引用、链接

页面由 `app.py` 末尾的 `app.mount("/", StaticFiles(...))` 托管；因为挂在最后，
`/docs`、`/chat` 等接口仍然优先匹配。

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

25 个用例全部离线：假模型客户端 + `TestClient` + `tmp_path` 临时数据库，
不联网、不需要真实 Key，也不会碰开发者本地的 `.env` 和 `chat.db`。

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_db.py` | 建表与外键、同一会话历史连续、会话隔离、清空后消息消失、重开数据库仍在、启动自动建库 |
| `tests/test_api_chat.py` | 连续对话带上历史、会话不串、学习功能、空消息被拒、响应不含 Key |
| `tests/test_api_sessions.py` | 会话列表、消息记录、清空后 404、不存在的会话 404 |
| `tests/test_api_stream.py` | 模型收到 `stream=True`、流式内容正确、流式回复写入历史 |
| `tests/test_web_ui.py` | 首页可访问、接口文档未被静态挂载挡住、未知路径 404 |
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

**请求返回 502**

模型调用失败（Key 错、余额不足、网络不通）。服务端只返回异常类型，不会泄露 Key。

**数据库被占用 / database is locked**

同一个 `chat.db` 被另一个进程写入；关闭另一个服务进程再试。
