import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import { MOCK_CAMERAS, makeMockPredictions } from './mock'

const SELECT = 'id, predicted_for, probability, species(*), camera:cameras(*)'

// The ML job's sample file (SYNTHETIC) stores times as offsets from when it was generated; show them
// relative to the visitor's "now". Returns null if the file is missing or not in the expected shape.
function fromSample(json) {
  const list = json?.predictions
  if (!Array.isArray(list) || list.length === 0) return null
  const now = Date.now()
  return list
    .map((p) => ({
      id: p.id,
      predicted_for: new Date(now + p.offset_minutes * 60 * 1000).toISOString(),
      probability: p.probability,
      species: p.species,
      camera: p.camera ? { ...p.camera, id: MOCK_CAMERAS.find((c) => c.name === p.camera.name)?.id ?? p.camera.name } : null,
    }))
    .sort((a, b) => a.predicted_for.localeCompare(b.predicted_for))
}

// Upcoming predictions, soonest first. With no Supabase keys: the ML job's sample file if present,
// else hard-coded samples. The card shows a "sample predictions" badge either way.
export function usePredictions() {
  const [predictions, setPredictions] = useState(() => (supabase ? [] : makeMockPredictions()))
  const [loading, setLoading] = useState(!!supabase)

  useEffect(() => {
    let cancelled = false
    if (!supabase) {
      fetch('/predictions.sample.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((json) => {
          const sample = fromSample(json)
          if (sample && !cancelled) setPredictions(sample)
        })
        .catch(() => {}) // keep the hard-coded fallback
      return () => {
        cancelled = true
      }
    }
    // Keep predictions that are still "now-ish" (15 min grace) so the next one doesn't vanish early
    const since = new Date(Date.now() - 15 * 60 * 1000).toISOString()
    supabase
      .from('predictions')
      .select(SELECT)
      .gte('predicted_for', since)
      .order('predicted_for', { ascending: true })
      .limit(5)
      .then(({ data, error }) => {
        if (error) console.error(error)
        if (cancelled) return
        setPredictions(data ?? [])
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { predictions, loading, usingMock: !supabase }
}
