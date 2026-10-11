import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase } from './supabase'

// A thread is the rows of `table` where `col` = `val`: a park's chat room (chat_messages.park) or the
// comments on one sighting (comments.sighting_id). Live through Supabase Realtime; with no keys it is
// an in-memory mock shared between tabs of the same browser via BroadcastChannel.

const LIMIT = 100
const mockStore = new Map() // key -> messages, kept for the life of the page
const bus = typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel('animal-logger-social')

const add = (list, msg) => (list.some((m) => m.id === msg.id) ? list : [...list, msg].slice(-LIMIT))

export function useThread(table, col, val, seed = []) {
  const key = `${table}:${val}`
  // Two mounted copies of the same thread must not share a realtime channel: supabase-js hands back the existing
  // (already joined) channel for a repeated topic, and adding callbacks to it throws.
  const instance = useRef(Math.random().toString(36).slice(2, 8))
  const [messages, setMessages] = useState(() => (supabase ? [] : (mockStore.get(key) ?? seed)))
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!supabase) {
      if (!mockStore.has(key)) mockStore.set(key, seed)
      setMessages(mockStore.get(key))
      const onMsg = (e) => {
        if (e.data.key !== key) return
        mockStore.set(key, add(mockStore.get(key) ?? [], e.data.msg))
        setMessages(mockStore.get(key))
      }
      bus?.addEventListener('message', onMsg)
      return () => bus?.removeEventListener('message', onMsg)
    }

    let cancelled = false
    setMessages([])
    supabase
      .from(table)
      .select('*')
      .eq(col, val)
      .order('created_at', { ascending: true })
      .limit(LIMIT)
      .then(({ data, error: err }) => {
        if (cancelled) return
        if (err) setError(err.message)
        else setMessages(data ?? [])
      })
    const channel = supabase
      .channel(`${key}:${instance.current}`)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table, filter: `${col}=eq.${val}` }, (p) => {
        if (!cancelled && !p.new.is_hidden) setMessages((prev) => add(prev, p.new))
      })
      .subscribe()
    return () => {
      cancelled = true
      supabase.removeChannel(channel)
    }
    // seed is only a first-load default; re-subscribing on every render would loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  // Returns an error message string, or null on success.
  const post = useCallback(
    async (name, body) => {
      if (!supabase) {
        const msg = { id: `mock-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, [col]: val, display_name: name, body, created_at: new Date().toISOString() }
        mockStore.set(key, add(mockStore.get(key) ?? [], msg))
        setMessages(mockStore.get(key))
        bus?.postMessage({ key, msg })
        return null
      }
      const { data, error: err } = await supabase.from(table).insert({ [col]: val, display_name: name, body }).select().single()
      if (err) return err.message
      setMessages((prev) => add(prev, data))
      return null
    },
    [table, col, val, key],
  )

  return { messages, post, error, usingMock: !supabase }
}
