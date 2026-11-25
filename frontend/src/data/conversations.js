/**
 * 演示数据：前端还没有接后端 /chat 接口（见 backend/README.md 的接口契约）。
 * 这里用本地数据把界面撑起来，形状与 GET /sessions/{id}/messages 的响应保持一致：
 * { role: 'user' | 'assistant', content: string, time: string }
 */
export const seedConversations = [
  {
    id: 's1',
    title: 'SQLAlchemy 事务边界',
    preview: '为什么模型调用要放在事务外面？',
    updatedAt: '刚刚',
    messages: [
      { role: 'user', content: '为什么模型调用要放在事务外面？', time: '10:24' },
      {
        role: 'assistant',
        content:
          '一次模型调用可能耗时几秒，而 SQLite 同一时刻只允许一个写事务。如果把它包在事务里，其他请求的写入会一直排队。\n\n所以正确的顺序是：先只读地取出历史，在内存里拼上本轮提问，模型返回后再用一个事务把“提问 + 回复”一起写入。\n\n这样既有原子性，又不会长时间占着写锁。',
        time: '10:24',
      },
      { role: 'user', content: '那代码大概长什么样？', time: '10:25' },
      {
        role: 'assistant',
        content:
          '核心就是 append_turn：两次 INSERT 在同一个 Session 里，最后一次提交。\n\n\u0060\u0060\u0060python\ndef append_turn(self, session_id, user_content, assistant_content):\n    now = utc_now_iso()\n    with self._scope() as session:\n        self._ensure_session(session, session_id, now)\n        self._insert_message(session, session_id, "user", user_content, now)\n        session.flush()\n        self._insert_message(session, session_id, "assistant", assistant_content, now)\n        self._touch_session(session, session_id, now)\n\u0060\u0060\u0060\n\n任何一步失败都会整体回滚，不会留下“只有提问没有回答”的半轮对话。',
        time: '10:25',
      },
    ],
  },
  {
    id: 's2',
    title: '给聊天页加关键词搜索',
    preview: 'GET /sessions/{id}/messages?keyword=',
    updatedAt: '今天 09:40',
    messages: [
      { role: 'user', content: '历史消息的关键词查询怎么做的？', time: '09:38' },
      {
        role: 'assistant',
        content:
          '接口是 GET /sessions/{session_id}/messages?keyword=索引，不传就返回完整历史。\n\n仓储层用 ORM 表达式过滤，编译出来是 LIKE，并且用 autoescape 把 % 和 _ 转义成普通字符：\n\n\u0060\u0060\u0060sql\nSELECT messages.role, messages.content\nFROM messages\nWHERE messages.session_id = ?\n  AND (messages.content LIKE \u0027%\u0027 || ? || \u0027%\u0027 ESCAPE \u0027/\u0027)\nORDER BY messages.id;\n\u0060\u0060\u0060\n\n排序仍然是 id 升序，所以命中结果与完整历史的相对顺序一致。',
        time: '09:40',
      },
    ],
  },
  {
    id: 's3',
    title: 'Vue 组件怎么拆',
    preview: '一个聊天页拆成几个组件合适？',
    updatedAt: '昨天',
    messages: [
      { role: 'user', content: '一个聊天页拆成几个组件合适？', time: '20:11' },
      {
        role: 'assistant',
        content:
          '按“谁拥有状态、谁只负责展示”来拆，不要按像素区域硬切。\n\n- 容器组件持有会话列表、当前会话、发送状态\n- 展示组件只接收 props、抛出事件：侧边栏、消息气泡、输入框、空状态\n\n这样状态变化只在一个地方发生，展示组件可以单独调试，也方便后面接入真实接口时替换数据源。',
        time: '20:12',
      },
    ],
  },
  {
    id: 's4',
    title: '新的对话',
    preview: '',
    updatedAt: '昨天',
    messages: [],
  },
]

export const demoReplies = [
  '收到。当前是前端演示模式，消息还没有发给后端；接入 /chat 之后这里会显示模型回复。',
  '这是一条本地示例回复：界面、主题和交互都可以先跑起来，等接口接通再替换数据源。',
  '好的，我记下了。真正接入时，这里会按 /chat/stream 的流式响应逐字渲染。',
]
