import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

const LiveContext = createContext(null)
const FRESH_MS = 6000
const RETRY_MS = 2000
const STALE_MS = 25000

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

    let source = null
    let retry = null
    let stopped = false
    let lastSeen = Date.now()
    const seen = () => { lastSeen = Date.now() }

    const reconnect = () => {
      source?.close()
      setConnected(false)
      setError('No hay conexión con el backend, reintentando…')
      clearTimeout(retry)
      retry = setTimeout(connect, RETRY_MS)
    }

    // Every (re)connection loads the full state again, since the backend may have restarted.
    function connect() {
      if (stopped) return
      seen()
      source = new EventSource('/api/stream')
      source.onopen = () => { seen(); setConnected(true); sync() }
      source.onerror = () => {
        setConnected(false)
        // The browser gives up after an error response (e.g. 502 while the backend is down), so retry by hand.
        if (source.readyState === EventSource.CLOSED) reconnect()
      }
      source.addEventListener('ping', seen)
      source.addEventListener('post_added', (event) => { seen(); addPost(JSON.parse(event.data)) })
      source.addEventListener('posts_reset', (event) => { seen(); setPosts(JSON.parse(event.data)) })
      source.addEventListener('model_changed', (event) => {
        seen()
        const { active_model } = JSON.parse(event.data)
        setMeta((current) => current && { ...current, active_model })
      })
    }

    // A proxy can keep a dead stream open; without the backend's heartbeat for too long, reconnect.
    const watchdog = setInterval(() => {
      if (Date.now() - lastSeen > STALE_MS) reconnect()
    }, 5000)

    connect()
    return () => {
      stopped = true
      clearTimeout(retry)
      clearInterval(watchdog)
      source?.close()
    }
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
