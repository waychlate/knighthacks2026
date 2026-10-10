import SightingCard from './components/SightingCard'
import { useSightings } from './lib/useSightings'

export default function App() {
  const { sightings, loading, usingMock } = useSightings()

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto max-w-2xl px-4 py-5">
          <h1 className="text-2xl font-bold text-stone-900">🦌 Animal Logger</h1>
          <p className="text-sm text-stone-500">Recent wildlife sightings from the park cameras</p>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {usingMock && (
          <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            Showing mock data. Add Supabase keys to <code>.env</code> to see real sightings.
          </p>
        )}

        {loading ? (
          <p className="text-stone-500">Loading…</p>
        ) : sightings.length === 0 ? (
          <p className="text-stone-500">No sightings yet. Check back soon.</p>
        ) : (
          <ul className="space-y-3">
            {sightings.map((s) => (
              <SightingCard key={s.id} sighting={s} />
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
