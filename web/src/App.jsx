import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ErrorBanner from './components/ErrorBanner'
import BearLoading from './components/BearLoading'
import ModeToggle from './components/ModeToggle'
import CameraPage from './pages/CameraPage'
import SettingsPage from './pages/SettingsPage'
import ParkPage from './pages/ParkPage'
import { filterByMode } from './lib/live'
import { useCameras } from './lib/useCameras'
import { useMode } from './lib/useMode'
import { useRoute } from './lib/useRoute'
import { useSightings } from './lib/useSightings'
import { markWelcomeSeen } from './lib/welcome'

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

function AppShell({ children, route, openSettings }) {
  const katmai = route.name === 'park' && route.park === 'katmai'
  const yellowstone = route.name === 'park' && route.park === 'yellowstone'
  return (
    <div className={`app-shell min-h-screen bg-stone-50 ${katmai ? 'katmai-page' : ''} ${yellowstone ? 'yellowstone-page' : ''}`}>
      <header className="app-header border-b border-stone-200 bg-white">
        <div className="mx-auto grid max-w-6xl grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-3 sm:py-4">
          <a href="#/" className="flex min-w-0 items-center gap-3 justify-self-start" aria-label="En-Vision globe home">
            <img src={katmai ? '/icons/icon-katmai.svg' : yellowstone ? '/icons/icon-yellowstone.svg' : '/icons/icon-192.svg'} alt="" className="app-logo h-11 w-11 shrink-0 rounded-xl" />
            <span className="min-w-0"><span className="block truncate text-xl font-bold text-stone-900 sm:text-2xl">En-Vision</span><span className="hidden text-sm text-stone-500 sm:block">Wildlife, seen together</span></span>
          </a>
          <a href="#/" className={`globe-pill ${route.name === 'park' ? 'globe-pill-desktop' : ''}`}>← 🌍 Globe</a>
          <div className="flex flex-wrap items-center gap-2 justify-self-end"><ModeToggle /><button type="button" onClick={openSettings} aria-label="Settings" title="Settings" className={`flex h-9 w-9 items-center justify-center rounded-lg border border-stone-300 bg-white text-lg text-stone-600 hover:bg-stone-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${route.name === 'park' ? 'hidden sm:flex' : ''}`}>⚙</button></div>
        </div>
      </header>
      <NetworkStatus />
      <main className="app-main mx-auto max-w-6xl px-4 py-5 sm:py-6">{children}</main>
    </div>
  )
}

// Short bear splash when moving between the globe and a park (either way), not on first load or park to camera moves.
function useParkSplash(route) {
  const [splash, setSplash] = useState(false)
  const prev = useRef(route)
  useEffect(() => {
    const was = prev.current
    prev.current = route
    const crossing = (was.name === 'globe') !== (route.name === 'globe') && (was.name === 'park' || route.name === 'park')
    if (!crossing || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    setSplash(true)
    const t = setTimeout(() => setSplash(false), 900)
    return () => clearTimeout(t)
  }, [route.name, route.park]) // eslint-disable-line react-hooks/exhaustive-deps
  return splash
}

export default function App() {
  const route = useRoute()
  const splash = useParkSplash(route)
  if (route.name !== 'globe') markWelcomeSeen() // deep links skip the welcome screen
  const { mode } = useMode()
  const { sightings: all, loading, usingMock, error: sightingsError } = useSightings()
  const { cameras, error: camerasError } = useCameras()
  const sightings = useMemo(() => filterByMode(all, mode), [all, mode])

  const [settingsOpen, setSettingsOpen] = useState(false)
  const openSettings = useCallback(() => setSettingsOpen(true), [])
  useEffect(() => {
    window.addEventListener('envision:open-settings', openSettings)
    return () => window.removeEventListener('envision:open-settings', openSettings)
  }, [openSettings])
  const closeSettings = useCallback(() => setSettingsOpen(false), [])
  const settings = settingsOpen && <SettingsPage onClose={closeSettings} />
  const overlay = splash && <div className="bear-splash"><BearLoading /></div>

  if (route.name === 'globe') return <>{overlay}<Suspense fallback={<BearLoading />}><GlobePage sightings={sightings} cameras={cameras} /></Suspense></>

  return <>{overlay}{settings}<AppShell route={route} openSettings={openSettings}><ErrorBanner errors={[sightingsError, camerasError]} />{usingMock && <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">Showing sample park data. Add Supabase keys to <code>.env</code> to see real sightings.</p>}{route.name === 'park' && <ParkPage slug={route.park} tab={route.tab} sightings={sightings} cameras={cameras} loading={loading} mode={mode} />}{route.name === 'camera' && <CameraPage id={route.id} sightings={sightings} cameras={cameras} loading={loading} mode={mode} />}</AppShell></>
}
