const BASE = import.meta.env.VITE_API_URL || ''

export async function fetchState() {
  const r = await fetch(`${BASE}/api/state`)
  if (!r.ok) throw new Error(`API ${r.status}`)
  return r.json()
}
