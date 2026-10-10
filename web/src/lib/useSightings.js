import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import { makeMockHistory, makeMockSighting } from './mock'

const LIMIT = 50
// '*' keeps working before and after the source_kind column exists
const SELECT = '*, species(*), camera:cameras(*)'

// Returns the most recent sightings (all modes; the app filters by Demo/Live), newest first, kept live.
// Uses Supabase Realtime when configured, otherwise a mock generator.
export function useSightings() {
  const [sightings, setSightings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const usingMock = !supabase

  useEffect(() => {
    if (!supabase) {
      setSightings(makeMockHistory())
      setLoading(false)
      const timer = setInterval(() => {
        setSightings((prev) => [makeMockSighting(), ...prev].slice(0, LIMIT))
      }, 6000)
      return () => clearInterval(timer)
    }

    let cancelled = false

    supabase
      .from('sightings')
      .select(SELECT)
      .order('seen_at', { ascending: false })
      .limit(LIMIT)
      .then(({ data, error }) => {
        if (cancelled) return
        if (error) setError(error.message)
        setSightings(data ?? [])
        setLoading(false)
      })

    const channel = supabase
      .channel('sightings-feed')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'sightings' }, async (payload) => {
        // Realtime payloads have no joins, so re-fetch the new row with species + camera
        const { data } = await supabase.from('sightings').select(SELECT).eq('id', payload.new.id).single()
        if (data && !cancelled) setSightings((prev) => [data, ...prev].slice(0, LIMIT))
      })
      .subscribe()

    return () => {
      cancelled = true
      supabase.removeChannel(channel)
    }
  }, [])

  return { sightings, loading, usingMock, error }
}
