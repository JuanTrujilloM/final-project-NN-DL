import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

const LiveContext = createContext(null)
const FRESH_MS = 6000

// Shared state for every view: metadata, posts and the live stream from the backend (SSE).
export function LiveProvider({ children }) {
  const [meta, setMeta] = useState(null)
  const [posts, setPosts] = useState([])
  const [connected, setConnected] = useState(false)
  const [fresh, setFresh] = useState({})
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const markFresh = useCallback((id) => {
    setFresh((current) => ({ ...current, [id]: Date.now() }))
    setTimeout(() => setFresh((current) => Object.fromEntries(Object.entries(current).filter(([key]) => key !== id))), FRESH_MS)
  }, [])

  const addPost = useCallback((post) => {
    setPosts((current) => (current.some((p) => p.id === post.id) ? current : [post, ...current]))
    markFresh(post.id)
  }, [markFresh])

  useEffect(() => {
    const sync = () => Promise.all([api.meta(), api.posts()])
      .then(([m, p]) => { setMeta(m); setPosts(p); setError(null) })
      .catch((e) => setError(e.message))

    // Every (re)connection loads the full state again, since the backend may have restarted.
    const source = new EventSource('/api/stream')
    source.onopen = () => { setConnected(true); sync() }
    source.onerror = () => setConnected(false)
    source.addEventListener('post_added', (event) => addPost(JSON.parse(event.data)))
    source.addEventListener('posts_reset', (event) => setPosts(JSON.parse(event.data)))
    source.addEventListener('model_changed', (event) => {
      const { active_model } = JSON.parse(event.data)
      setMeta((current) => current && { ...current, active_model })
    })
    return () => source.close()
  }, [addPost])

  const run = useCallback(async (kind, action) => {
    setBusy(kind)
    setError(null)
    try {
      return await action()
    } catch (e) {
      setError(e.message)
      throw e
    } finally {
      setBusy(null)
    }
  }, [])

  const value = useMemo(() => {
    const groupsById = Object.fromEntries((meta?.groups ?? []).map((g) => [g.id, g]))
    const modelsById = Object.fromEntries((meta?.models ?? []).map((m) => [m.id, m]))
    return {
      meta, posts, connected, fresh, busy, error, groupsById, modelsById,
      activeModel: meta ? modelsById[meta.active_model] : null,
      clearError: () => setError(null),
      publish: (text) => run('publish', async () => {
        const post = await api.publish({ text })
        addPost(post)
        return post
      }),
      setModel: (id) => run('model', async () => setMeta(await api.setModel(id))),
      reclassify: () => run('reclassify', async () => setPosts(await api.reclassify())),
    }
  }, [meta, posts, connected, fresh, busy, error, run, addPost])

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>
}

export function useLive() {
  return useContext(LiveContext)
}
