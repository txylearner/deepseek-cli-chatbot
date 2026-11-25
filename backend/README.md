# DeepSeek 对话机器人（FastAPI + SQLite + SQLAlchemy ORM）

第 2 次作业是命令行聊天机器人，第 3 次把它改造成 HTTP 服务，第 4 次把会话搬进 SQLite 并按分层架构拆分，
第 5 次用 SQLAlchemy 2.x ORM 接管数据库访问，一轮对话写进同一个事务，并支持按关键词查历史消息；
第 6 次只做工程整理：后端整体搬进 `backend/`，仓库根另建一个空的 Vue 3 前端工程（见根目录 README）。

> **本目录是后端项目**：`pytest`、`uvicorn`、`scripts/build_frontend.py` 等命令都必须在 `backend/` 目录下执行。
> `.env`、`chat.db`、`src/chatbot/static/` 都是相对当前工作目录或包目录解析的。

## 本次改造点

| 作业要求 | 实现位置 |
|---|---|
| 为“会话”“消息”定义 ORM 模型（主键、外键、relationship） | `db/models.py` |
| 字段与已有 SQLite 表对应，启动不删表、不清库 | `db/schema.py`（`create_all(checkfirst=True)`） |
| 存储模块改用 ORM 完成会话创建、列表、历史、清空、消息写入 | `repositories/session_repository.py` |
| 每次数据库操作显式打开和关闭 Session | `db/engine.py` 的 `session_scope` |
| 一轮对话的用户消息与助手回复写在同一事务 | `services/chat_service.py` + `append_turn()` |
| 历史消息按关键词查询（ORM 查询表达式） | `api/sessions.py`、`repositories/session_repository.py` |
| 网页里能搜历史消息 | `webui/js/app.js` + `search-bar` 样式 |
| 离线测试：旧数据可读、事务回滚、关键词查询 | `tests/` 共 51 个用例 |
| README 说明模型与数据表的对应关系，并给出 ORM 查询对应的 SQL | 本文「数据库」一节 |

## 功能

- `POST /chat` 一问一答，按 `session_id` 维护多轮历史
- `POST /chat/stream` 流式输出（`StreamingResponse` 逐块返回）
- `GET /sessions`、`GET /sessions/overview`、`GET /sessions/{id}/messages`、`DELETE /sessions/{id}`
- `GET /sessions/{id}/messages?keyword=` 按关键词查历史（只查当前会话，顺序与原历史一致）
- `POST /study/word` 学习功能：英语单词讲解
- 会话与消息写入 SQLite，服务重启后历史仍在
- 一问一答的提问与回复**在同一个事务里落库**：写失败时整轮回滚，不会留下半轮对话
- 网页聊天界面：会话列表（消息数 + 最近时间）、历史消息、新建 / 切换 / 清空、
  逐字输出、Markdown 渲染、深浅色主题
- 中英文一键切换（`EN` / `中`），界面文案、空状态、提示与 toast 同步切换
- 独立「背景颜色」面板：经典蓝 / 樱花粉 / 青绿色 / 樱花青绿渐变，和深浅色互不冲突
- 侧边栏品牌、欢迎页、助手头像与 favicon 使用鲸鱼娘图标
- 51 个离线测试

## 环境要求

- Python 3.12+
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

## 安装

~~~powershell
cd backend
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
如果目录里已经有一个第 4 次作业留下的 `chat.db`，它会**原样继续用**，旧聊天记录照样能读。

## 项目结构

~~~text
.
├── pyproject.toml
├── .env.example
├── webui/                        # 聊天页源码（不直接对外托管）
│   ├── index.html                # 页面结构
│   ├── css/app.css               # 样式
│   ├── js/app.js                 # 交互逻辑
│   └── assets/whale.png          # 鲸鱼娘图标（构建时转 base64 内联）
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
│   ├── services/                 # 业务层：编排顺序与事务边界
│   │   ├── chat_service.py
│   │   └── study_service.py
│   ├── repositories/             # 仓库层：唯一读写数据的地方
│   │   └── session_repository.py # ORM 查询表达式 + 工作单元
│   ├── db/                       # 数据库层
│   │   ├── models.py             # ORM 模型：sessions / messages
│   │   ├── engine.py             # 引擎、Session 工厂、PRAGMA、事务
│   │   └── schema.py             # 建表入口（create_all）
│   ├── models/                   # Pydantic 请求 / 响应模型
│   │   └── schemas.py
│   ├── core/                     # 配置、提示词、领域异常、时间格式
│   │   ├── clock.py
│   │   ├── config.py
│   │   ├── prompts.py
│   │   └── exceptions.py
│   ├── llm/                      # DeepSeek 调用
│   │   └── deepseek.py
│   ├── cli/                      # 命令行版（与 Web 共用 Service / Repository）
│   │   └── main.py
│   └── static/
│       └── index.html            # 聊天页构建产物（浏览器实际拿到的页面）
└── tests/
    ├── conftest.py               # 假模型 + 临时数据库
    ├── test_orm_store.py         # 表结构 / 旧库兼容 / 重开连接 / 聚合 / 级联
    ├── test_transaction.py       # 一轮两条消息 / 写失败回滚 / 模型失败
    ├── test_message_search.py    # 关键词查询：命中 / 顺序 / 隔离 / 通配符转义
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
- **services**：校验输入、决定什么时候调模型、什么时候开事务
- **repositories**：唯一读写会话与消息的地方，接口由 `SessionRepository` 约定
- **db**：ORM 模型、连接参数（外键开关、超时）、Session 工厂与建表

换数据库时，只需要新增一个实现 `SessionRepository` 的类，并在 `app.py` 里替换构造。

### 事务边界：模型调用在事务之外

一次普通对话的顺序是：

~~~text
读历史（只读事务） → 拼上本轮提问 → 调模型（不占事务） → 一个事务写两条消息
~~~

- `append_turn()` 把用户消息与助手回复放在同一个 Session 里，最后一次提交
- 任何一步失败都会整体回滚，连会话记录都一起撤销，不会留下“只有提问没有回答”的半轮
- 模型调用不放进事务：一次调用可能耗时数秒，而 SQLite 同一时刻只允许一个写事务，
  长事务会让其他请求全部排队

### 并发与性能

- 路由全部是同步 `def`：FastAPI 会把它丢进线程池，阻塞的 SQLAlchemy 调用不会卡住事件循环。
  如果把同步 Session 塞进 `async def`，并发会退化成串行
- 每次操作开一个短 Session，数据库引擎按库文件缓存连接池，进程内复用
- 连接上显式发 `BEGIN`：pysqlite 默认只在 DML 前开启事务，会让 `SAVEPOINT` 变成最外层事务、
  `RELEASE` 时被提前提交，嵌套事务因此失效
- 连接参数：`PRAGMA foreign_keys = ON`、`busy_timeout = 5000`，外键约束与锁等待都由数据库兜底

## 数据库

- 文件：默认 `chat.db`，可用环境变量 `CHATBOT_DB_PATH` 改路径
- 建表：`db/schema.py` 里调用 `Base.metadata.create_all()`，仓库初始化时执行，可重复运行
- 读写：全部集中在 `repositories/session_repository.py`，路由和 Service 里没有 SQL
- 数据库文件已被 `.gitignore` 忽略，不会提交

### 模型与数据表的对应关系

| ORM 模型 | 数据表 | 字段（列名 : 类型） | 说明 |
|---|---|---|---|
| `ChatSession` | `sessions` | `id` TEXT 主键；`created_at`、`updated_at` TEXT | 一行一个会话；`messages` 关系指向它的消息 |
| `ChatMessage` | `messages` | `id` INTEGER 主键自增；`session_id` TEXT 外键；`role`、`content`、`created_at` TEXT | `session` 关系指回会话；外键 `ON DELETE CASCADE` |

- `ChatSession.messages` 与 `ChatMessage.session` 通过 `back_populates` 双向绑定，
  拿到会话就能顺着关系取到它的消息，不用手写 join
- `passive_deletes=True`：删除会话时不逐条加载消息，交给数据库的 `ON DELETE CASCADE`
- 外键约束需要每条连接都打开（SQLite 默认关闭），这一步挂在 `db/engine.py` 的 connect 事件上
- 字段类型使用 `Text` / `Integer`，新库生成的 DDL 与第 4 次作业逐列对应，
  由 `tests/test_orm_store.py::test_orm_creates_the_same_table_layout` 守住

### ER 图

下面这张图和 `db/models.py` 的模型声明一一对应：

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

- 一个会话对应零到多条消息，消息通过 `session_id` 外键指向 `sessions.id`
- 删除会话时，`ON DELETE CASCADE` 会把它的消息一起删掉
- `idx_messages_session` 让“按会话取历史”走索引，而不是全表扫描

### 一条 ORM 查询与它的 SQL

关键词查询（`GET /sessions/{id}/messages?keyword=索引`）在仓储里的写法：

~~~python
stmt = (
    select(ChatMessage.role, ChatMessage.content)
    .where(ChatMessage.session_id == session_id)
    .order_by(ChatMessage.id)
)
if keyword:
    stmt = stmt.where(ChatMessage.content.contains(keyword, autoescape=True))
rows = session.execute(stmt).all()
~~~

它编译出来、真正发给 SQLite 的语句是：

~~~sql
SELECT messages.role, messages.content
FROM messages
WHERE messages.session_id = ?
  AND (messages.content LIKE '%' || ? || '%' ESCAPE '/')
ORDER BY messages.id;
~~~

手写 SQL 时，同样的语义会写成：

~~~sql
SELECT id, session_id, role, content, created_at
FROM messages
WHERE session_id = :session_id
  AND content LIKE '%' || :keyword || '%' ESCAPE '/'
ORDER BY id;
~~~

两种写法的关系：

- ORM 表达式是**同一件事的另一种描述**：`select().where()` 只说“查哪张表、过滤什么、怎么排序”，
  由 SQLAlchemy 在编译阶段翻译成参数化 SQL（`?` 占位符）再交给 SQLite；两者执行的是同一条语句
- 关键词永远走占位符，不在 ORM 里拼字符串，所以带引号、分号也不会变成 SQL 语法
- `contains(keyword, autoescape=True)` 会多生成 `ESCAPE '/'`，把关键词里的 `%` `_` 转义成普通字符；
  否则搜 `100%` 会退化成通配符匹配，把所有消息都捞出来
- 性能上两者完全一致：都走 `idx_messages_session` 的 `(session_id, id)` 前缀；
  `LIKE '%关键词%'` 开头的 `%` 让它用不上 `content` 上的索引（本次也没有给 `content` 建索引，
  真要做全文检索应该上 SQLite 的 FTS5，而不是继续加 B-tree 索引）

### 升级到 ORM 时，旧数据怎么办

第 4 次作业的 `chat.db` 不需要搬迁，也不需要写脚本：

- 模型字段与旧表逐列对应，表结构没变，所以**没有表结构迁移**
- 启动时用的是 `create_all(checkfirst=True)`：表已存在就一条 DDL 都不发，
  既不删表也不清库，旧的 `sessions` / `messages` 原样保留
- `tests/test_orm_store.py` 里有一条用例专门用第 4 次作业的 DDL 建库、灌数据、
  再用 ORM 打开，断言旧记录可读且 `sqlite_master` 里的建表语句一个字节都没变

如果以后确实要加列（例如给消息加 `token_count`），`create_all` 不会帮你改已有表，
那时需要引入版本化迁移（Alembic，或手写 `schema_version` 表配升级/回滚脚本）。

### 验证“重启不丢数据”

~~~powershell
# 1. 发一条消息
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"u1\",\"message\":\"我叫小明\"}"

# 2. Ctrl+C 停掉服务，再重新启动
python -m uvicorn chatbot.app:app --port 8000

# 3. 历史仍在
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages
~~~

## 聊天页：源码与构建产物分离

`webui/` 里是可以阅读、修改的源码；浏览器不会直接拿到它。

~~~powershell
# 改完 webui/ 后重新构建（在 backend/ 目录下执行）
python scripts/build_frontend.py

# 只检查产物是否最新（CI 用）
python scripts/build_frontend.py --check
~~~

构建脚本做四件事：

1. 把 `css/app.css` 和 `js/app.js` 内联进 `index.html`
2. 把 `assets/whale.png` 转成 base64，用于 CSS 变量和 favicon
3. 用 `rjsmin` 压缩 JavaScript，去掉注释与空白
4. 输出到 `src/chatbot/static/index.html`，由 FastAPI 托管

浏览器最终收到的是压缩后的单文件，看不到 `webui/` 的目录结构；
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
| GET | `/sessions/{session_id}/messages` | 某会话的消息记录，可加 `?keyword=` 按关键词过滤 |
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
curl.exe -s http://127.0.0.1:8000/sessions/u1/messages?keyword=索引
curl.exe -s -X DELETE http://127.0.0.1:8000/sessions/u1
~~~

查询不存在的会话返回 **404**。

`keyword` 不传或传空串时返回完整历史；传了就只返回当前会话里内容包含它的消息，
顺序与完整历史一致。关键词最长 100 个字符，超了返回 **422**。

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
- 右上角 **搜索** 打开历史搜索条：输入关键词后只显示当前会话的命中消息并给出条数，
  **Esc** 或 **×** 退出搜索即恢复完整历史；发新消息前会自动退出搜索
- 右上角 **EN/中** 一键切换中英文；**背景** 打开背景颜色面板
- 背景颜色：经典蓝 / 樱花粉 / 青绿色 / 樱花青绿渐变，与深色 / 浅色相互独立
- 品牌标、欢迎页、助手头像与 favicon 使用鲸鱼娘图标
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

51 个用例全部离线：假模型客户端 + `TestClient` + `tmp_path` 临时数据库，
不联网、不需要真实 Key，也不会碰开发者本地的 `.env` 和 `chat.db`。

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_orm_store.py` | ORM 生成的表结构与旧库一致、旧库数据可读且建表语句不变、重开连接历史仍在、会话隔离、概览聚合、级联删除 |
| `tests/test_transaction.py` | 一轮对话恰好两条消息、写失败整轮回滚、API 返回 500 且不留数据、模型失败不落库 |
| `tests/test_message_search.py` | 不传关键词返回完整历史、命中过滤、顺序不变、跨会话隔离、`%` 不当通配符、空关键词、404、超长 422 |
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

没装依赖，在 `backend/` 目录下执行 `python -m pip install -e ".[dev]"`。

**`ModuleNotFoundError: No module named 'sqlalchemy'`**

本项目新增了 ORM 依赖，在 `backend/` 下重新执行一次 `python -m pip install -e ".[dev]"`。

**`ModuleNotFoundError: No module named 'chatbot'`**

不在 `backend/` 目录下，先 `cd backend` 再执行。

**`[Errno 10048] address already in use`**

8000 端口被占用，换一个：`--port 8001`。

**改了 webui/ 但页面没变**

忘记构建了，执行 `python scripts/build_frontend.py` 后刷新浏览器。

**请求返回 502**

模型调用失败（Key 错、余额不足、网络不通）。服务端只返回异常类型，不会泄露 Key。

**请求返回 500**

数据库写入失败：这一轮已经整体回滚，历史里不会留下半条消息，可以重试。
确认磁盘可写、`chat.db` 没有被别的进程长期占用。

**数据库被占用 / database is locked**

同一个 `chat.db` 被另一个进程写入；关闭另一个服务进程再试。
