async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Error ${response.status}`)
  return data
}

export const api = {
  meta: () => request('/api/meta'),
  posts: () => request('/api/posts'),
  publish: (body) => request('/api/posts', { method: 'POST', body: JSON.stringify(body) }),
  setModel: (model) => request('/api/active-model', { method: 'PUT', body: JSON.stringify({ model }) }),
  reclassify: () => request('/api/reclassify', { method: 'POST' }),
}
