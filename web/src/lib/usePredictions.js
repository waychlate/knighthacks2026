import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import { makeMockPredictions } from './mock'

const SELECT = 'id, predicted_for, probability, species(*), camera:cameras(*)'

// Upcoming predictions, soonest first. Mock samples until the ML job writes real rows.
export function usePredictions() {
  const [predictions, setPredictions] = useState(() => (supabase ? [] : makeMockPredictions()))
  const [loading, setLoading] = useState(!!supabase)

  useEffect(() => {
    if (!supabase) return
    let cancelled = false
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
