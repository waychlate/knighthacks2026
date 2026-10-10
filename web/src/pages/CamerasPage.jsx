import { cameraHref } from '../lib/useRoute'
import { timeAgo } from '../lib/time'

export default function CamerasPage({ sightings, cameras }) {
  if (cameras.length === 0) return <p className="text-stone-500">No cameras registered yet.</p>

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {cameras.map((cam) => {
        const mine = sightings.filter((s) => s.camera.id === cam.id) // newest first
        return (
          <li key={cam.id}>
            <a
              href={cameraHref(cam.id)}
              className="block rounded-xl border border-stone-200 bg-white p-4 shadow-sm hover:border-emerald-400"
            >
              <p className="font-semibold text-stone-900">📷 {cam.name}</p>
              {cam.location && <p className="text-sm text-stone-500">{cam.location}</p>}
              <p className="mt-3 text-sm text-stone-700">
                {mine.length} recent sighting{mine.length === 1 ? '' : 's'}
              </p>
              <p className="text-sm text-stone-500">
                {mine[0] ? `Last: ${mine[0].species.common_name}, ${timeAgo(mine[0].seen_at)}` : 'Nothing seen yet'}
              </p>
            </a>
          </li>
        )
      })}
    </ul>
  )
}
