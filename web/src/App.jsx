import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import ErrorBanner from './components/ErrorBanner'
import ModeToggle from './components/ModeToggle'
import ThemeToggle from './components/ThemeToggle'
import CameraPage from './pages/CameraPage'
import ParkPage from './pages/ParkPage'
import { filterByMode } from './lib/live'
import { useCameras } from './lib/useCameras'
import { useMode } from './lib/useMode'
import { useRoute } from './lib/useRoute'
import { useSightings } from './lib/useSightings'

const GlobePage = lazy(() => import('./pages/GlobePage'))

function NetworkStatus() {
  const [offline, setOffline] = useState(() => !navigator.onLine)
  const [update, setUpdate] = useState(false)
  useEffect(() => {
    const online = () => setOffline(false)
    const offlineState = () => setOffline(true)
    const showUpdate = () => setUpdate(true)
    window.addEventListener('online', online)
    window.addEventListener('offline', offlineState)
    window.addEventListener('envision:pwa-update', showUpdate)
    return () => {
      window.removeEventListener('online', online)
      window.removeEventListener('offline', offlineState)
      window.removeEventListener('envision:pwa-update', showUpdate)
    }
  }, [])
  if (!offline && !update) return null
  return <div className="status-banner" role="status"><span>{offline ? 'Offline: cached park data may be stale; fresh sightings may be delayed.' : 'A new En-Vision update is ready.'}</span><div className="flex items-center gap-2">{offline && <button type="button" className="status-action" onClick={() => window.location.reload()}>Retry</button>}{update && <button type="button" className="status-action" onClick={() => window.envisionUpdateSW?.(true)}>Update</button>}</div></div>
}

function AppShell({ children, route }) {
  const katmai = route.name === 'park' && route.park === 'katmai'
  const yellowstone = route.name === 'park' && route.park === 'yellowstone'
  return (
    <div className={`app-shell min-h-screen bg-stone-50 ${katmai ? 'katmai-page' : ''} ${yellowstone ? 'yellowstone-page' : ''}`}>
      <header className="app-header border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:py-4">
          <a href="#/" className="flex min-w-0 items-center gap-3" aria-label="En-Vision globe home">
            <img src={katmai ? '/icons/icon-katmai.svg' : yellowstone ? '/icons/icon-yellowstone.svg' : '/icons/icon-192.svg'} alt="" className="app-logo h-11 w-11 shrink-0 rounded-xl" />
            <span className="min-w-0"><span className="block truncate text-xl font-bold text-stone-900 sm:text-2xl">En-Vision</span><span className="hidden text-sm text-stone-500 sm:block">Wildlife, seen together</span></span>
          </a>
          <div className="flex flex-wrap items-center gap-2"><ThemeToggle /><ModeToggle /></div>
        </div>
      </header>
      <NetworkStatus />
      <main className="app-main mx-auto max-w-6xl px-4 py-5 sm:py-6">{children}</main>
    </div>
  )
}

export default function App() {
  const route = useRoute()
  const { mode } = useMode()
  const { sightings: all, loading, usingMock, error: sightingsError } = useSightings()
  const { cameras, error: camerasError } = useCameras()
  const sightings = useMemo(() => filterByMode(all, mode), [all, mode])

  if (route.name === 'globe') return <Suspense fallback={<div className="globe-loading"><span>Loading En-Vision globe…</span></div>}><GlobePage sightings={sightings} cameras={cameras} /></Suspense>

  return <AppShell route={route}><ErrorBanner errors={[sightingsError, camerasError]} />{usingMock && <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">Showing sample park data. Add Supabase keys to <code>.env</code> to see real sightings.</p>}{route.name === 'park' && <ParkPage slug={route.park} tab={route.tab} sightings={sightings} cameras={cameras} loading={loading} mode={mode} />}{route.name === 'camera' && <CameraPage id={route.id} sightings={sightings} cameras={cameras} loading={loading} mode={mode} />}</AppShell>
}
