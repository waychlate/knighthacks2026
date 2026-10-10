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
        Camera not found. <a className="text-emerald-700 underline" href="#/cameras">Back to cameras</a>
      </p>
    )
  }

  const name = camera?.name ?? mine[0]?.camera.name
  const location = camera?.location ?? mine[0]?.camera.location

  return (
    <>
      <a href="#/cameras" className="text-sm text-emerald-700 hover:underline">
        ← All cameras
      </a>
      <h2 className="mt-2 text-xl font-bold text-stone-900">📷 {name}</h2>
      {location && <p className="text-sm text-stone-500">{location}</p>}

      <div className="mt-4">
        <CameraPanel camera={{ name, ...camera }} />
      </div>

      {counts.length > 0 && (
        <div className="my-4 flex flex-wrap gap-2">
          {counts.map(({ species, n }) => (
            <span key={species.id} className="rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-800">
              {species.common_name} · {n}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4">
        <SightingList
          sightings={mine}
          loading={loading}
          emptyText={mode === 'live' ? 'Waiting for the first sighting from the live camera.' : 'Nothing seen on this camera yet.'}
        />
      </div>

      <div className="mt-6">
        <ChatPanel park={camera?.park ?? mine[0]?.camera.park ?? 'yellowstone'} />
      </div>
    </>
  )
}
