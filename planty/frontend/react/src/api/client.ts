const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_URL || API.replace('http://', 'ws://').replace('https://', 'wss://')

export async function request(path: string, method = 'GET', body?: unknown) {
  const token = localStorage.getItem('token')
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export { API, WS_BASE }
