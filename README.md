# DeepSeek 对话机器人（FastAPI 版）

第 2 次作业是命令行聊天机器人；这次把它改造成 **HTTP 服务**：支持多轮连续对话、流式输出、
会话管理和一个学习小功能，会话数据先放在内存里。

DeepSeek 提供 OpenAI 兼容接口，所以客户端仍然用 `openai` 包 + 自定义 `base_url`。

## 功能

- `POST /chat` 一问一答，按 `session_id` 维护多轮历史
- `GET /sessions`、`GET /sessions/{id}/messages`、`DELETE /sessions/{id}` 会话管理
- `POST /chat/stream` 流式输出（`stream=True` + `StreamingResponse`）
- `POST /study/word` 学习功能：英语单词讲解
- 配置集中在 `src/chatbot/config.py`，API Key 用 `SecretStr` 保护
- 自带一个简洁的网页聊天界面（侧边栏会话列表 + 流式打字 + Markdown 渲染）
- 16 个离线测试，不联网、不需要真实 API Key

## 环境要求

- Python 3.12+
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

## 安装

```powershell
cd "目标文件夹"
python -m pip install -e ".[dev]"
```

配置 Key（`.env` 已被 `.gitignore` 忽略，不会提交）：

```powershell
Copy-Item .env.example .env
```

```dotenv
CHATBOT_API_KEY=sk-你的真实Key
```

## 启动服务

```powershell
python -m uvicorn chatbot.app:app --reload --port 8000
```

- 浏览器打开 <http://127.0.0.1:8000/> 就是**聊天界面**（平时用这个）
- <http://127.0.0.1:8000/docs> 是接口文档，可以点 **Try it out** 逐个调试（答辩时给老师看）
- 健康检查：<http://127.0.0.1:8000/health>

## 网页聊天界面

打开 <http://127.0.0.1:8000/> 即可，不需要额外装前端工具、也不联网加载任何 CDN：

- 左侧是会话列表：**＋ 新对话**、点击切换历史会话、悬停出现 **×** 删除
- 中间是对话区：用户消息靠右显示气泡，助手回复靠左逐字流出（走 `POST /chat/stream`）
- 底部是输入框：**Enter 发送**、**Shift+Enter 换行**，生成中按钮变成 ■ 可随时停止
- 右上角 **清空** 删除当前会话，**☀️/🌙** 切换深色/浅色主题（记在 localStorage 里）
- 助手回复支持 Markdown：标题、粗体、列表、行内代码、代码块、引用、链接

实现只有一个文件 `src/chatbot/static/index.html`（HTML + CSS + 原生 JS，约 540 行），
由 `app.py` 末尾的 `app.mount("/", StaticFiles(...))` 提供；因为挂在最后，
`/docs`、`/chat` 等接口仍然优先匹配。

> 学习功能 `POST /study/word` 目前只提供接口，界面里没有入口（作业要求是"通过 API 提供"）。

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

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"hello\"}"
```

```json
{"session_id": "u1", "reply": "你好！有什么可以帮你？"}
```

同一个 `session_id` 再问一句，模型能看到之前的对话：

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"what did I just say?\"}"
```

### 2. 会话管理

```powershell
# 会话列表
curl.exe -s http://127.0.0.1:8000/sessions
# {"sessions": ["u1"]}

# 某会话的消息记录（按对话顺序）
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages
# {"session_id":"u1","messages":[{"role":"user","content":"hello"},{"role":"assistant","content":"..."}]}

# 清空会话
curl.exe -s -X DELETE http://127.0.0.1:8000/sessions/u1
# {"session_id":"u1","deleted":true}
```

查询不存在的会话返回 **404**。

### 3. 流式输出

```powershell
curl.exe -N -X POST http://127.0.0.1:8000/chat/stream -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"tell me a joke\"}"
```

`-N` 关闭缓冲，可以看到文字一段段出现；流结束后完整回复会被写进该会话历史。

### 4. 学习功能：单词讲解

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/study/word -H "Content-Type: application/json" -d "{\"word\":\"apple\"}"
```

```json
{"word": "apple", "explanation": "n. 苹果。例句：I ate an apple.（我吃了一个苹果。）"}
```

## 配置项

全部写在 `src/chatbot/config.py` 的 `Settings` 里，可被同名环境变量或 `.env` 覆盖。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CHATBOT_API_KEY` | 无（必填） | DeepSeek API Key |
| `CHATBOT_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `CHATBOT_MODEL` | `deepseek-chat` | 模型名，也可用 `deepseek-reasoner` |
| `CHATBOT_TEMPERATURE` | `0.7` | 采样温度，范围 0–2 |
| `CHATBOT_MAX_HISTORY` | `20` | 命令行版保留的最近轮数 |

## 测试

```powershell
python -m pytest -q
```

16 个用例全部离线：用 `TestClient` + 假模型客户端，不联网、不需要真实 Key。

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_api_chat.py` | 连续对话带上历史、会话不串、学习功能可调用、空消息被拒绝、响应不含 Key |
| `tests/test_api_sessions.py` | 会话列表、消息记录、清空后 404、不存在的会话 404 |
| `tests/test_api_stream.py` | 模型收到 `stream=True`、流式内容正确、流式回复写入历史 |
| `tests/test_config.py` | 配置默认值、温度越界、Key 不明文 |
| `tests/test_llm.py` | 传给模型的参数 |

## 项目结构

```text
.
├── pyproject.toml
├── .env.example
├── src/chatbot/
│   ├── app.py        # FastAPI 应用与路由（末尾挂载静态页面）
│   ├── static/
│   │   └── index.html  # 单文件聊天界面（HTML + CSS + 原生 JS）
│   ├── store.py      # 内存会话仓库（唯一读写会话的地方）
│   ├── study.py      # 学习功能：单词讲解提示词
│   ├── llm.py        # DeepSeek 调用（流式 + 一次性）
│   ├── config.py     # Settings / get_settings
│   ├── chat.py       # 命令行版遗留的 ChatSession
│   ├── main.py       # 命令行入口
│   └── __main__.py   # python -m chatbot
└── tests/
    ├── conftest.py
    ├── test_api_chat.py
    ├── test_api_sessions.py
    ├── test_api_stream.py
    ├── test_web_ui.py
    ├── test_config.py
    └── test_llm.py
```

## 命令行版仍可用

改造没有删掉原来的 CLI，调试时还能直接用：

```powershell
python -m chatbot
```

输入 `exit` 或 `quit` 退出。

## 安全注意

- `.env` 不要提交，提交前用 `git status` 检查
- API 响应里只有 `session_id`、`reply`、`role`、`content`，不含 Key
- 会话数据在内存里，重启服务即清空（后续可换 Redis / 数据库）
- `store.py` 是唯一读写会话的模块，换存储只改这一处

## 常见问题

**`ModuleNotFoundError: No module named 'fastapi'`**

没装依赖，在项目根目录执行 `python -m pip install -e ".[dev]"`。

**`ModuleNotFoundError: No module named 'chatbot'`**

不在项目根目录，先 `cd` 到本目录。

**`[Errno 10048] address already in use`**

8000 端口被占用，换一个：`--port 8001`。

**请求返回 502**

模型调用失败（Key 错、余额不足、网络不通）。服务端只返回异常类型，不会泄露 Key。

**中文乱码**

用 `/docs` 页面调试最稳；用 `curl.exe` 时确保终端是 UTF-8。
