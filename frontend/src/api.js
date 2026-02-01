const API_BASE = 'http://127.0.0.1:8765'

const API_CONNECT_MSG = '无法连接后端服务，请确认 API 已启动 (127.0.0.1:8765)。Tauri 启动时会自动拉取，若失败请单独运行: npm run api'

function wrapNetworkError(e) {
  if (e?.message === 'Failed to fetch' || e?.name === 'TypeError') {
    return new Error(API_CONNECT_MSG)
  }
  return e
}

export async function getTheme() {
  try {
    const r = await fetch(`${API_BASE}/api/theme`)
    const data = await r.json()
    return data.mode
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

export async function setTheme(mode) {
  try {
    const r = await fetch(`${API_BASE}/api/theme`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    })
    const data = await r.json()
    return data.mode
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

export async function normalize(body) {
  try {
    const r = await fetch(`${API_BASE}/api/normalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(await r.text())
    return r.json()
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

export async function watermark(body) {
  try {
    const r = await fetch(`${API_BASE}/api/watermark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(await r.text())
    return r.json()
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

/**
 * 流式调用 normalize，通过 onEvent 实时接收 log / progress / done
 * @param {object} body - 同 normalize
 * @param {(ev: { type: 'log'|'progress'|'done', msg?: string, value?: number, ok?: boolean, ok_count?: number, fail_count?: number, results?: object }) => void} onEvent
 */
export async function normalizeStream(body, onEvent) {
  try {
    const r = await fetch(`${API_BASE}/api/normalize/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(await r.text())
    const reader = r.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const line = part.split('\n').find(l => l.startsWith('data:'))
        if (!line) continue
        try {
          const data = JSON.parse(line.slice(5).trim())
          onEvent(data)
          if (data.type === 'done') return data
        } catch (_) {}
      }
    }
    return null
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

/**
 * 流式调用 watermark，通过 onEvent 实时接收 log / progress / done
 */
export async function watermarkStream(body, onEvent) {
  try {
    const r = await fetch(`${API_BASE}/api/watermark/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(await r.text())
    const reader = r.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const line = part.split('\n').find(l => l.startsWith('data:'))
        if (!line) continue
        try {
          const data = JSON.parse(line.slice(5).trim())
          onEvent(data)
          if (data.type === 'done') return data
        } catch (_) {}
      }
    }
    return null
  } catch (e) {
    throw wrapNetworkError(e)
  }
}

export async function merge(body) {
  try {
    const r = await fetch(`${API_BASE}/api/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(await r.text())
    return r.json()
  } catch (e) {
    throw wrapNetworkError(e)
  }
}
