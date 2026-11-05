# 第 3 次作业：Git 与 PR 操作指南

当前状态：两个功能分支已经在本地提交完毕，只差推送和开 PR。

| 分支 | 提交内容 | 对应 issue |
|---|---|---|
| `feat/fastapi-chat-sessions` | 会话存储、`POST /chat`、会话管理接口、依赖更新 | #5 |
| `feat/fastapi-stream-study` | `/chat/stream`、单词讲解、3 组离线测试、README | #6 |

---

## 0. 先在 GitHub 建 2 个 issue

仓库 → **Issues** → **New issue**：

1. 标题 `实现 FastAPI 对话接口与会话管理`
2. 标题 `实现流式输出、学习功能与离线测试`

记下两个编号（大概率是 **#5**、**#6**）。

---

## 1. 推送分支 A 并开 PR

```powershell
cd "C:\Users\谭新宇\Desktop\智能AI应用作业\第3次作业"
git switch feat/fastapi-chat-sessions
git push -u origin feat/fastapi-chat-sessions
```

仓库首页会出现 **Compare & pull request**，点它，标题填：

```text
feat: FastAPI 对话接口与会话管理
```

描述：

```markdown
## 改了什么
- 新增内存会话存储模块 store.py，所有读写集中在这一处，方便以后换数据库
- 新增 POST /chat，按 session_id 维护多轮历史
- 新增 GET /sessions、GET /sessions/{id}/messages、DELETE /sessions/{id}
- llm.py 增加 complete_chat，把流式片段拼成完整回复
- 依赖补充 fastapi、uvicorn、httpx

## 怎么验证
- python -m uvicorn chatbot.app:app --port 8000，用 /docs 逐个调用
- 同 session_id 追问能接上历史；换 session_id 不串话
- 查不存在的会话返回 404，空消息返回 400

Closes #5
```

→ **Create pull request** → 请同学在 **Files changed** 留一条 review → 你回复 →
**Merge pull request**（选 **Create a merge commit**）。

---

## 2. 合并后推送分支 B

```powershell
git switch main
git pull --ff-only
git switch feat/fastapi-stream-study
git push -u origin feat/fastapi-stream-study
```

同样开 PR：

```text
feat: 流式输出、学习功能与离线测试
```

```markdown
## 改了什么
- 新增 POST /chat/stream，用 StreamingResponse 边收边发，结束后把完整回复写回历史
- 新增 POST /study/word 学习功能（单词讲解）
- 新增 3 组离线测试：对话、会话管理、流式输出，共 10 个用例
- README 补充服务启动方法与全部接口示例

## 怎么验证
- python -m pytest -q（13 个用例全部通过，不联网、不需要真实 Key）
- curl -N 调用 /chat/stream，可以看到文字一段段出现
- 流式结束后 GET /sessions/{id}/messages 能看到这条回复

Closes #6
```

review → 回复 → **Create a merge commit**。

---

## 3. 合并后收尾

```powershell
git switch main
git pull --ff-only
git log --graph --oneline --all --decorate
```

截图存档；确认：

- [ ] 两个 PR 都是「功能分支 → main」，都写了 `Closes #x`
- [ ] 两个 PR 都有 review 评论 + 你的回复
- [ ] main 已开启分支保护（Settings → Branches → Require a pull request before merging）
- [ ] `git log` 能看到两个 merge commit
- [ ] 仓库里没有 `.env`、没有真实 Key

---

## 4. 常见错误

- **`git add .`**：会把 `.env`、`chatbot_api.txt`、笔记一起提交。只 `git add` 具体文件。
- **Squash merge**：`git log --graph` 看不到分支图形，作业要求的是合并提交。
- **直接 push main**：分支保护会拦；如果没配保护，说明要去 Settings 打开。
- **PR 只改 README**：属于凑数 PR，作业明确不允许。
- **忘记 `Closes #x`**：issue 不会自动关联，老师会认为没关联 issue。
