import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import { MOCK_CAMERAS } from './mock'

export function useCameras() {
  const [cameras, setCameras] = useState(supabase ? [] : MOCK_CAMERAS)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!supabase) return
    let cancelled = false
    supabase
      .from('cameras')
      .select('*')
      .order('name')
      .then(({ data, error }) => {
        if (cancelled) return
        if (error) setError(error.message)
        setCameras((data ?? []).map((c) => ({ park: 'yellowstone', ...c })))
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { cameras, error }
}
