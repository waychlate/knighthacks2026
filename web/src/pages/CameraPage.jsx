import { useMemo } from 'react'
import CameraPanel from '../components/CameraPanel'
import ChatPanel from '../components/ChatPanel'
import SightingList from '../components/SightingList'

export default function CameraPage({ id, sightings, cameras, loading, mode }) {
  const camera = cameras.find((c) => c.id === id)
  const mine = useMemo(() => sightings.filter((s) => s.camera.id === id), [sightings, id])

  // Species seen on this camera, most frequent first
  const counts = useMemo(() => {
    const map = new Map()
    for (const s of mine) {
      const entry = map.get(s.species.id) ?? { species: s.species, n: 0 }
      entry.n += 1
      map.set(s.species.id, entry)
    }
    return [...map.values()].sort((a, b) => b.n - a.n)
  }, [mine])

  if (!loading && !camera && mine.length === 0) {
    return (
      <p className="text-stone-500">
        Camera not found. <a className="text-emerald-700 underline" href="#/park/yellowstone/cameras">Back to cameras</a>
      </p>
    )
  }

  const name = camera?.name ?? mine[0]?.camera.name
  const location = camera?.location ?? mine[0]?.camera.location
  const park = camera?.park ?? mine[0]?.camera.park ?? 'yellowstone'
  const themeClass = park === 'katmai' ? 'katmai-theme' : 'forest-theme'

  return (
    <div className={`${themeClass} px-2 py-2 sm:px-6 sm:py-4`}>
      <a href={`#/park/${park}/cameras`} className="back-button">
        <span className="back-arrow" aria-hidden>←</span> All cameras
      </a>
      <h2 className="mt-2 text-xl font-bold text-stone-900">📷 {name}</h2>
      {location && <p className="text-sm text-stone-500">{location}</p>}

      <div className="mt-4 grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)] lg:items-start">
        <section>
          <CameraPanel camera={{ name, ...camera }} />

          {counts.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {counts.map(({ species, n }) => (
                <span key={species.id} className="rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-800">
              {species.common_name} · {n}
                </span>
              ))}
            </div>
          )}

        </section>

        <section>
          <h3 className="mb-3 text-lg font-semibold text-stone-900">Detected animals</h3>
          <SightingList
            sightings={mine}
            loading={loading}
            emptyText={mode === 'live' ? 'Waiting for the first sighting from the live camera.' : 'Nothing seen on this camera yet.'}
          />
        </section>
      </div>

      <ChatPanel park={park} />
    </div>
  )
}
