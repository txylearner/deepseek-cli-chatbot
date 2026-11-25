/** 展示用的时间格式：聊天里只关心“刚刚 / 今天 10:24 / 昨天 / 10 月 3 日”。 */

function pad(value) {
  return String(value).padStart(2, '0')
}

export function nowClock() {
  const date = new Date()
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatRelative(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''

  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (seconds < 60) return '刚刚'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`

  const clock = `${pad(date.getHours())}:${pad(date.getMinutes())}`
  if (date.toDateString() === now.toDateString()) return `今天 ${clock}`

  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return `昨天 ${clock}`

  return `${date.getMonth() + 1} 月 ${date.getDate()} 日`
}
