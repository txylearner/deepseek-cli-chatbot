# DeepSeek 命令行聊天机器人

一个用于课程作业的简易 AI Agent：通过 DeepSeek 的 OpenAI 兼容接口进行多轮对话，并支持流式输出。

## 功能

- 多轮连续对话，始终保留 system prompt
- 流式输出（调用模型时开启 `stream=True`，逐块打印）
- 使用 `pydantic-settings` 从环境变量和 `.env` 读取配置
- API Key 使用 `SecretStr`，打印配置时不会出现明文
- 缺少 API Key 时给出可读提示并退出
- 自动裁剪历史，默认保留最近 20 轮
- 两个完全离线的 pytest 测试模块，不需要真实 API Key

## 环境要求

- Python 3.12+
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

## 快速开始

> 先进入**项目根目录**，也就是能看到 `pyproject.toml`、`src`、`tests` 的那个目录。下面所有命令都必须在这里执行；在 `C:\Windows\System32` 等目录执行会把当前目录误当成项目。

### 1. 创建虚拟环境并安装

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

如果 PowerShell 不允许激活脚本，可以先在当前终端临时放开：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Windows cmd：

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

### 2. 配置 API Key

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，把 `CHATBOT_API_KEY` 换成自己的 DeepSeek Key：

```dotenv
CHATBOT_API_KEY=sk-你的真实Key
```

> `.env` 已被 `.gitignore` 忽略，不会被提交；`.env.example` 只放占位符，可以提交。

### 3. 运行

```powershell
python -m chatbot
```

安装后也可以直接使用命令入口：

```powershell
chatbot
```

输入内容开始对话，输入 `exit` 或 `quit` 退出。

### 4. 运行测试

```powershell
python -m pytest -q
```

测试不联网、不需要真实 API Key。

## 在 WSL/Ubuntu 中运行

如果使用 VS Code 的 WSL 插件，建议把项目复制到 Ubuntu 家目录（例如 `~/projects/chatbot`），不要在 `/mnt/c` 里直接开发，也不要把 Windows 的 `.venv` 复制过去（Windows 的 `Scripts` 目录在 Linux 下不可用）。

先确认你已经进入 WSL：提示符应该是 `txy@主机名:~$` 这样的 Linux 提示符，而不是 `PS C:\Windows\System32>`。`sudo`、`source`、`python3.12` 都是 Linux 命令，在 PowerShell 里不能直接执行。

在 Ubuntu 终端中执行：

```bash
mkdir -p ~/projects/chatbot
cp -a "/mnt/c/Users/<Windows用户名>/Desktop/智能AI应用作业/第2次作业/." ~/projects/chatbot/
cd ~/projects/chatbot

# 删除 Windows 生成的虚拟环境和缓存
rm -rf .venv .pytest_cache
find . -type d -name "__pycache__" -prune -exec rm -rf {} +

python3 --version
sudo apt update
sudo apt install -y python3.12 python3.12-venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

cp .env.example .env
nano .env        # 填入 CHATBOT_API_KEY
python -m pytest -q
python -m chatbot
```

如果 `python3.12` 不存在，说明 Ubuntu 版本较旧（例如 22.04 默认是 3.10）；本作业要求 3.12，请先确认系统版本并安装 Python 3.12，不要直接用 3.10 建环境。

复制完成后，用 VS Code 打开 WSL 中的项目：

```bash
cd ~/projects/chatbot
code .
```

VS Code 左下角应显示 `WSL: Ubuntu`，集成终端应是 Linux bash，而不是 PowerShell。

## 配置项

所有可变参数都集中在 `src/chatbot/config.py` 的 `Settings` 中，运行时可被 `.env` 或同名环境变量覆盖。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CHATBOT_API_KEY` | 无（必填） | DeepSeek API Key |
| `CHATBOT_BASE_URL` | `https://api.deepseek.com` | DeepSeek 的 OpenAI 兼容接口地址 |
| `CHATBOT_MODEL` | `deepseek-chat` | 模型名，也可改为 `deepseek-reasoner` |
| `CHATBOT_TEMPERATURE` | `0.7` | 采样温度，范围 0–2；设为 5 会抛 `ValidationError` |
| `CHATBOT_MAX_HISTORY` | `20` | 保留最近多少轮对话 |

## 项目结构

```text
.
├── pyproject.toml
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── chatbot/
│       ├── __init__.py
│       ├── __main__.py      # python -m chatbot 入口
│       ├── config.py        # Settings / get_settings
│       ├── llm.py           # DeepSeek client / stream_chat
│       ├── chat.py          # ChatSession / 历史裁剪
│       └── main.py          # CLI 入口
├── tests/
│   ├── test_config.py
│   └── test_llm.py
└── docs/
    └── PR_GUIDE.md
```

## 实现说明

### 配置

`Settings` 使用 `CHATBOT_` 前缀，因此 `CHATBOT_API_KEY` 会自动映射到 `api_key` 字段。`get_settings()` 带 `lru_cache`，测试中通过 `get_settings.cache_clear()` 隔离配置。

`get_settings()` 本身不捕获 `ValidationError`，这样测试可以断言：

```python
with pytest.raises(ValidationError):
    get_settings()
```

友好的“缺少 API Key”提示放在 `main.run()` 中，由 CLI 层负责。

### 流式输出

`stream_chat()` 逐块读取 DeepSeek 的 SSE 响应，只把 `delta.content` 交给 CLI。CLI 使用：

```python
print(delta, end="", flush=True)
```

因此不会每个片段都换行；整轮结束后只打印一个换行。

### 历史裁剪

`ChatSession.trim_history()` 始终保留第一条 system prompt，只裁剪较早的对话，避免长对话无限增长，也避免出现“只有 assistant 没有对应 user”的孤立消息。

### 测试如何做到离线

`tests/test_llm.py` 不创建真实 `OpenAI` 客户端，而是注入一个假的 client，直接断言传给模型的参数：

- `model` 与配置一致
- `temperature` 与配置一致
- `messages` 是包含 `role`/`content` 的字典列表
- `stream` 必须为 `True`

## 安全注意

- 不要把 `.env` 提交到 Git；提交前执行 `git status` 检查。
- 不要在日志、截图或 PR 描述中粘贴真实 API Key。
- `SecretStr` 只能防止“直接打印配置”时泄露，不能防止在代码中显式调用 `get_secret_value()`，因此只应在构造 API 客户端时读取明文 Key。

## 常见问题

**`ModuleNotFoundError: No module named 'chatbot'`**

先确认在项目根目录执行了：

```powershell
python -m pip install -e ".[dev]"
```

**`pip install -e .` 报 `C:\Windows\System32 does not appear to be a Python project`**

说明你不在项目根目录。先退出当前虚拟环境，再进入项目目录：

```powershell
deactivate
cd "C:\Users\谭新宇\Desktop\智能AI应用作业\第2次作业"
Get-ChildItem pyproject.toml
```

看到 `pyproject.toml` 后，重新创建并激活项目自己的 `.venv`。**不要**在 `C:\Windows\System32` 里继续执行 `pip install -e .`。

**`pytest` 扫描到 `C:\Windows\System32\LogFiles` 并报 PermissionError**

原因同样是没有进入项目目录：`pytest` 把整个 `System32` 当成测试目录了。用 `cd` 进入项目根目录，并改用当前虚拟环境的解释器执行：

```powershell
python -m pytest -q
```

确认虚拟环境已激活，且当前目录是项目根目录；不要直接运行单个测试文件而不安装项目。

**缺少 API Key**

复制 `.env.example` 为 `.env`，填入 `CHATBOT_API_KEY`。程序会提示缺少配置并以非零状态退出，不会打印一大段 traceback。

**WSL 里 pip 报 `files.pythonhosted.org ... Network is unreachable`**

这是 WSL 访问 PyPI 文件服务器失败，不是代码问题。使用国内镜像重试：

```bash
cd ~/projects/chatbot
source .venv/bin/activate
python -m pip install -e ".[dev]" \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --trusted-host pypi.tuna.tsinghua.edu.cn \
  --timeout 120 --retries 5
```

如果清华镜像也慢，可以换阿里云：

```bash
-i https://mirrors.aliyun.com/pypi/simple/
```

不要把 `openai` 的上限去掉；本作业固定使用 `openai>=1.40.0,<2.0.0`，避免 pip 在 3.x 上反复回溯。
