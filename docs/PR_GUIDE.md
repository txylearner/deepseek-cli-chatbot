# Git 提交与 PR 操作指南

当前工作区已经是**完整实现**。为了满足作业“至少 2 个功能分支 PR、不能一次性提交全部代码”的要求，请按模块拆分提交，**不要执行 `git add .`**。

拆分思路：

- 初始骨架：项目配置、依赖、忽略规则、README、包初始化
- PR 1：配置模块 + 对话状态模块（library 层）
- PR 2：DeepSeek 调用、流式 CLI、两个离线测试

---

## 0. 创建仓库与初始提交

先在 GitHub 创建一个**空仓库**（不要勾选 Add a README file），然后：

```powershell
git init -b main
git add pyproject.toml .gitignore .env.example README.md src/chatbot/__init__.py docs/PR_GUIDE.md
git commit -m "chore: scaffold Python project"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

推送后立刻设置分支保护：

> GitHub 仓库 → Settings → Branches → Add branch protection rule → 分支名 `main` → 勾选 **Require a pull request before merging** → Save。

如果你一个人做，不要勾选“必须 1 个 approve”，否则自己无法合并自己的 PR；但作业要求的“至少 1 条 review 评论”仍要请同学/助教留，或在 PR 的 Files changed 里留一条具体评论后回复。

> 初始骨架直接推送到 main 是为了建立基线；之后的功能代码都必须走 PR。

---

## 1. PR 1：配置与对话状态

先建 issue #1，例如标题：

```text
实现 pydantic-settings 配置与多轮对话状态
```

然后：

```powershell
git switch -c feat/config-and-chat

git add src/chatbot/config.py
git commit -m "feat(config): add pydantic-settings configuration"

git add src/chatbot/chat.py
git commit -m "feat(chat): add conversation state and history trimming"

git push -u origin feat/config-and-chat
```

在 GitHub 上创建 PR：`feat/config-and-chat` → `main`。

PR 描述模板：

```markdown
## 改了什么
- 新增 pydantic-settings 配置，统一管理模型、Base URL、API Key、温度和历史轮数
- 新增 ChatSession，负责 system prompt、多轮消息和历史裁剪
- API Key 使用 SecretStr，打印配置不会出现明文

## 怎么验证
- `python -c "from chatbot.chat import ChatSession; s=ChatSession(); s.add_user('你好'); print(s.build_messages())"`
- 确认 `print(get_settings())` 不包含真实 Key

Closes #1
```

> PR 1 是配置与对话状态层，CLI 和模型调用在 PR 2 接入。

请同学/助教留至少 1 条 review 评论，并回复；然后用 **Create a merge commit** 合并，不要用 Squash。

---

## 2. PR 2：流式输出与离线测试

先建 issue #2，例如标题：

```text
接入 DeepSeek 流式输出并补齐两个离线测试
```

从最新的 main 开分支：

```powershell
git switch main
git pull --ff-only
git switch -c feat/stream-and-tests

git add src/chatbot/llm.py
git commit -m "feat(llm): stream DeepSeek chat completions"

git add src/chatbot/main.py src/chatbot/__main__.py
git commit -m "feat(cli): add interactive command-line loop"

git add tests/test_config.py
git commit -m "test(config): cover defaults and SecretStr masking"

git add tests/test_llm.py
git commit -m "test(llm): assert model parameters and stream=True"

git push -u origin feat/stream-and-tests
```

在 GitHub 上创建 PR：`feat/stream-and-tests` → `main`。

PR 描述模板：

```markdown
## 改了什么
- 使用 OpenAI 兼容 SDK 调用 DeepSeek，开启 stream=True 并逐块输出
- 新增 CLI 交互循环，支持多轮对话、错误提示和安全退出
- 新增两个离线 pytest 测试：配置解析、模型调用参数

## 怎么验证
- `python -m pytest -q`（3 个用例全部通过）
- 手动运行 `python -m chatbot`，观察逐字输出，连续对话 3 轮
- 删除 .env 后启动，确认输出可读的缺少 Key 提示

Closes #2
```

同样请人 review、回复评论，然后用 **Create a merge commit** 合并。

---

## 3. 最终检查

```powershell
git switch main
git pull --ff-only
python -m pytest -q
git log --graph --oneline --all --decorate
```

确认：

- `main` 上能看到两个 PR 的 merge commit
- `.env` 没有被 Git 跟踪：`git ls-files | Select-String ".env"`
- `.env.example` 在仓库里
- `git log --graph --oneline --all` 截图已保存
- PR 描述都写了 `Closes #1` / `Closes #2`
- 每个 PR 至少有 1 条 review 评论和回复

---

## 4. 常见错误

- `git add .`：会把 PR 2 的代码一次性带进 PR 1，违反拆分要求
- 直接 push main：分支保护会阻止；如果没阻止，说明保护没开
- Squash merge：`git log --graph --all` 看不到分支历史，建议用 merge commit
- 把 `.env` 提交：立刻 `git rm --cached .env`，并确认 `.gitignore` 生效
- PR 只改 README：作业明确不允许凑数 PR
