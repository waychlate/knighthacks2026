import Nav from './components/Nav'
import CameraPage from './pages/CameraPage'
import CamerasPage from './pages/CamerasPage'
import FeedPage from './pages/FeedPage'
import { useCameras } from './lib/useCameras'
import { useRoute } from './lib/useRoute'
import { useSightings } from './lib/useSightings'

export default function App() {
  const route = useRoute()
  const { sightings, loading, usingMock } = useSightings()
  const cameras = useCameras()

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-3 px-4 py-5">
          <div>
            <h1 className="text-2xl font-bold text-stone-900">🦌 Animal Logger</h1>
            <p className="text-sm text-stone-500">Recent wildlife sightings from the park cameras</p>
          </div>
          <Nav route={route} />
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {usingMock && (
          <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            Showing mock data. Add Supabase keys to <code>.env</code> to see real sightings.
          </p>
        )}

        {route.name === 'feed' && <FeedPage sightings={sightings} cameras={cameras} loading={loading} />}
        {route.name === 'cameras' && <CamerasPage sightings={sightings} cameras={cameras} />}
        {route.name === 'camera' && (
          <CameraPage id={route.id} sightings={sightings} cameras={cameras} loading={loading} />
        )}
      </main>
    </div>
  )
}
