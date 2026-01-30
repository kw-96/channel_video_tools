const API_BASE = 'http://127.0.0.1:8765'

export async function getTheme() {
  const r = await fetch(`${API_BASE}/api/theme`)
  const data = await r.json()
  return data.mode
}

export async function setTheme(mode) {
  const r = await fetch(`${API_BASE}/api/theme`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
  const data = await r.json()
  return data.mode
}

export async function normalize(body) {
  const r = await fetch(`${API_BASE}/api/normalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function watermark(body) {
  const r = await fetch(`${API_BASE}/api/watermark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function merge(body) {
  const r = await fetch(`${API_BASE}/api/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
