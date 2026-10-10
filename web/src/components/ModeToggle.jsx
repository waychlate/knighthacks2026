import { useEffect, useState } from 'react'
import { useMode } from '../lib/useMode'

const base = 'px-3 py-1.5 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500'

export default function ModeToggle() {
  const { mode, setMode } = useMode()
  const [offline, setOffline] = useState(() => !navigator.onLine)
  useEffect(() => {
    const online = () => setOffline(false)
    const offlineState = () => setOffline(true)
    window.addEventListener('online', online)
    window.addEventListener('offline', offlineState)
    return () => { window.removeEventListener('online', online); window.removeEventListener('offline', offlineState) }
  }, [])
  return (
    <div role="group" aria-label="Data source" className="inline-flex overflow-hidden rounded-lg border border-stone-300">
      {[
        ['demo', 'Demo'],
        ['live', 'Live'],
      ].map(([value, label]) => (
        <button
          key={value}
          type="button"
          aria-pressed={mode === value}
          onClick={() => setMode(value)}
          className={`${base} ${
            mode === value
              ? value === 'live'
                ? 'bg-emerald-600 text-white'
                : 'bg-amber-500 text-white'
              : 'bg-white text-stone-600 hover:bg-stone-100'
          }`}
        >
          {value === 'live' && offline ? 'Live · offline' : label}
        </button>
      ))}
    </div>
  )
}
