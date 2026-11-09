# 第 4 次作业：Git 与 PR 操作指南

当前状态：两个功能分支已经在本地提交完毕，只差推送和开 PR。

| 分支 | 提交数 | 内容 |
|---|---|---|
| `feat/db-persistence` | 4 | 分层重构、SQLite 存储、数据库测试、README |
| `feat/web-frontend` | 4 | 会话概览接口、前端源码与构建、前端测试、README |

`main` 仍停在第 3 次作业合并后的状态，等两个 PR 合入。

> 网络提示：本机目前解析不了 `github.com`（`git ls-remote` 会报
> `Could not resolve host`）。推送前先开代理 / VPN，或者换一台网络正常的电脑。
> 先在项目目录执行一次下面这条命令，能列出分支就说明网络通了：
>
> ~~~powershell
> git ls-remote --heads https://github.com/txylearner/deepseek-cli-chatbot
> ~~~

---

## 0. 先建 2 个 issue

仓库 → **Issues** → **New issue**：

1. 标题：`会话存储改为 SQLite 持久化`
2. 标题：`前端源码分离与聊天页面升级`

记下两个编号（大概率是 **#11**、**#12**）。下面 PR 描述里的 `Closes #11` 要换成真实编号。

---

## 1. 推送分支 A 并开 PR

~~~powershell
cd "C:\Users\谭新宇\Desktop\智能AI应用作业\第4次作业"
git switch feat/db-persistence
git push -u origin feat/db-persistence
~~~

打开仓库首页，会出现 **Compare & pull request**，标题填：

~~~text
feat: 会话存储改为 SQLite 持久化
~~~

描述：

~~~markdown
## 改了什么
- 后端按 Controller / Service / Repository 分层，路由不再直接操作数据
- 会话与消息改存 SQLite：新增 db/ 包，启动时自动建表
- 消息表通过外键指向会话表，删除会话时级联删除消息
- 数据库文件加入 .gitignore，测试使用 tmp_path 临时库
- 新增 9 个数据库测试，覆盖建表、历史、隔离、清空、重启

## 怎么验证
- python -m pytest -q（25 passed）
- 启动服务发一条消息，Ctrl+C 重启后
  GET /sessions/{id}/messages 仍能查到原记录

Closes #11
~~~

→ **Create pull request** → 在 **Files changed** 留一条 review（例如：确认
`store` 是唯一写 SQL 的地方）→ 你回复 → **Merge pull request**（选
**Create a merge commit**，不要 Squash）。

---

## 2. 合并后同步分支 B

~~~powershell
git switch main
git pull --ff-only
git switch feat/web-frontend
git merge main
git push -u origin feat/web-frontend
~~~

`git merge main` 把刚合入的数据库改动带到 B 分支，避免 PR 里出现重复提交。

同样开 PR，标题：

~~~text
feat: 前端源码分离与聊天页面升级
~~~

描述：

~~~markdown
## 改了什么
- 前端源码移到 frontend/，浏览器只拿到构建后的单文件页面
- 新增 scripts/build_frontend.py：内联 CSS/JS 并用 rjsmin 压缩
- 新增 GET /sessions/overview，侧边栏显示首条提问、消息数、最近时间
- 页脚与空状态提示数据已写入 SQLite
- README 增加 mermaid ER 图、建表语句与前端构建说明
- 测试补充前端托管与源码不暴露的断言（31 passed）

## 怎么验证
- python scripts/build_frontend.py 后刷新页面
- 浏览器访问 / 能聊天；查看网页源代码只有压缩后的单文件
- 直接访问 /css/app.css、/js/app.js 返回 404
- python -m pytest -q（31 passed）

Closes #12
~~~

review → 回复 → **Create a merge commit**。

---

## 3. 合并后收尾

~~~powershell
git switch main
git pull --ff-only
git log --graph --oneline --all --decorate -20
~~~

确认：

- [ ] 两个 PR 都是「功能分支 → main」，描述里写了 `Closes #x`
- [ ] 两个 PR 都有 review 评论 + 你的回复
- [ ] `git log --graph` 能看到两个 merge commit
- [ ] 仓库里没有 `.env`、没有 `*.db`
- [ ] 合并后的 main 能跑 `python -m pytest -q`（31 passed）
- [ ] 浏览器打开 8000 端口能看到聊天页面

---

## 4. 常见错误

- **直接 push main**：分支保护会拦；没配保护就在 Settings → Branches 打开
  “Require a pull request before merging”。
- **Squash merge**：`git log --graph` 看不到分支图形，作业要求是合并提交。
- **PR 只改 README**：这次两个 PR 都有真实功能和测试，不要拆成“凑数 PR”。
- **忘记重新构建前端**：改了 `frontend/` 一定要跑
  `python scripts/build_frontend.py`，否则页面还是旧的。
- **提交了 `.env` 或 `chat.db`**：`git status` 检查；已提交的话用
  `git rm --cached .env` 移出跟踪。
- **网络不通就反复重试**：先确认 `git ls-remote` 能解析域名，再推送。
