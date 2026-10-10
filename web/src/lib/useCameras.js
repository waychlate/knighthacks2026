import { useEffect, useState } from 'react'
import { supabase } from './supabase'
import { MOCK_CAMERAS } from './mock'

export function useCameras() {
  const [cameras, setCameras] = useState(supabase ? [] : MOCK_CAMERAS)

  useEffect(() => {
    if (!supabase) return
    let cancelled = false
    supabase
      .from('cameras')
      .select('*')
      .order('name')
      .then(({ data, error }) => {
        if (error) console.error(error)
        if (!cancelled) setCameras(data ?? [])
      })
    return () => {
      cancelled = true
    }
  }, [])

  return cameras
}
