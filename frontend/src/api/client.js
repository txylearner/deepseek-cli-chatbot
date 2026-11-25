/**
 * 后端接口封装：路径与 backend/README.md 的接口清单一致。
 *
 * 开发期由 Vite 代理把 /chat、/sessions 转发到 http://127.0.0.1:8000（见 vite.config.js），
 * 所以这里一律写相对路径：同源部署时不用改任何代码。
 */

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readError(response) {
  try {
    const data = await response.json()
    if (data && typeof data.detail === 'string' && data.detail) return data.detail
  } catch {
    /* 不是 JSON，继续读文本 */
  }
  try {
    const text = await response.text()
    if (text) return text.slice(0, 200)
  } catch {
    /* 忽略读取失败 */
  }
  return `HTTP ${response.status}`
}

async function request(path, options) {
  const response = await fetch(path, options)
  if (!response.ok) throw new ApiError(await readError(response), response.status)
  return response.json()
}

/** GET /sessions/overview -> { sessions: [{ id, title, message_count, updated_at }] } */
export function fetchOverview() {
  return request('/sessions/overview')
}

/** GET /sessions/{id}/messages(?keyword=) -> { session_id, messages: [{ role, content }] } */
export function fetchMessages(sessionId, keyword) {
  const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''
  return request(`/sessions/${encodeURIComponent(sessionId)}/messages${query}`)
}

/** DELETE /sessions/{id}：不存在时也当成功（404 会被后端语义化返回） */
export async function deleteSession(sessionId) {
  const response = await fetch(`/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
  if (!response.ok && response.status !== 404) {
    throw new ApiError(await readError(response), response.status)
  }
}

/**
 * POST /chat/stream：逐块读取纯文本，边读边把累积内容交给 onDelta。
 * 返回完整回复；调用方传入 signal 可以用 AbortController 中断。
 */
export async function streamChat({ sessionId, message, signal, onDelta }) {
  const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  })
  if (!response.ok) throw new ApiError(await readError(response), response.status)
  if (!response.body) throw new ApiError('当前浏览器不支持流式读取响应', 0)

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let answer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    answer += chunk
    if (onDelta) onDelta(chunk, answer)
  }
  return answer
}
