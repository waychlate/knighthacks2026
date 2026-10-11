import { useSyncExternalStore } from 'react'

const QUERY = '(max-width: 639px)' // matches the phone breakpoint in index.css

export const useIsPhone = () =>
  useSyncExternalStore(
    (cb) => {
      const m = window.matchMedia(QUERY)
      m.addEventListener('change', cb)
      return () => m.removeEventListener('change', cb)
    },
    () => window.matchMedia(QUERY).matches,
  )
