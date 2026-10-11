import { useCallback, useEffect, useMemo, useState } from 'react'
import { addDemoPin, useDemoPins } from './demoPins'
import { makeSamplePings, recent, roundCoord } from './pings'
import { supabase } from './supabase'

// Real pings (Supabase, live via Realtime; with no keys, only the ones posted in this tab) plus,
// in Demo mode only, clearly flagged sample pings.
export function usePings(mode) {
  const [real, setReal] = useState([])
  const [error, setError] = useState(null)
  const samples = useMemo(() => makeSamplePings(), [])
  const demoPins = useDemoPins()

  useEffect(() => {
    if (!supabase) return
    let cancelled = false
    const since = new Date(Date.now() - 24 * 3600e3).toISOString()
    supabase
      .from('pings')
      .select('*')
      .gte('created_at', since)
      .order('created_at', { ascending: false })
      .limit(500)
      .then(({ data, error: err }) => {
        if (cancelled) return
        if (err) setError(err.message)
        else setReal(data ?? [])
      })
    const channel = supabase
      .channel('pings')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'pings' }, (p) => {
        if (!cancelled && !p.new.is_hidden) setReal((prev) => (prev.some((x) => x.id === p.new.id) ? prev : [p.new, ...prev]))
      })
      .subscribe()
    return () => {
      cancelled = true
      supabase.removeChannel(channel)
    }
  }, [])

  // Returns an error message string, or null on success. Coordinates are rounded here too.
  // `demo: true` keeps the ping in this browser only (see demoPins.js); it is never sent to Supabase.
  const post = useCallback(async ({ lat, lng, species_name, note }, { demo = false } = {}) => {
    const row = { lat: roundCoord(lat), lng: roundCoord(lng), species_name: species_name || null, note: note || null }
    if (demo) {
      addDemoPin(row)
      return null
    }
    if (!supabase) {
      setReal((prev) => [{ ...row, id: `local-${Date.now()}`, created_at: new Date().toISOString() }, ...prev])
      return null
    }
    const { data, error: err } = await supabase.from('pings').insert(row).select().single()
    if (err) return err.message
    setReal((prev) => (prev.some((x) => x.id === data.id) ? prev : [data, ...prev]))
    return null
  }, [])

  const pings = useMemo(() => recent(mode === 'demo' ? [...real, ...samples, ...demoPins] : real), [real, samples, demoPins, mode])
  return { pings, post, error, usingMock: !supabase }
}
