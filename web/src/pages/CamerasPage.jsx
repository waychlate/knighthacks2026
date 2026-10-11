import { hasLiveFeed } from '../lib/cameraConfig'
import { cameraHref } from '../lib/useRoute'
import { timeAgo } from '../lib/time'
import { useMode } from '../lib/useMode'

export default function CamerasPage({ sightings, cameras, park }) {
  const { mode } = useMode()
  const leafCardClass = park === 'yellowstone' || park === 'katmai' ? `${park}-camera-card` : ''
  if (cameras.length === 0) return <p className="text-stone-500">No cameras registered yet.</p>

  return (
    <ul className="camera-grid grid gap-3 sm:grid-cols-2">
      {cameras.map((cam) => {
        const mine = sightings.filter((s) => s.camera.id === cam.id) // newest first
        const unavailable = mode === 'live' && !hasLiveFeed(cam)
        const body = (
          <>
            <p className="font-semibold text-stone-900">{park === 'katmai' ? '🐻' : '📷'} {cam.name}</p>
            {cam.location && <p className="text-sm text-stone-500">{cam.location}</p>}
            {unavailable ? (
              <p className="mt-3 text-sm text-stone-500">No live feed. Switch to Demo to see a recorded clip.</p>
            ) : (
              <>
                <p className="mt-3 text-sm text-stone-700">
                  {mine.length} recent sighting{mine.length === 1 ? '' : 's'}
                </p>
                <p className="text-sm text-stone-500">
                  {mine[0] ? `Last: ${mine[0].species.common_name}, ${timeAgo(mine[0].seen_at)}` : 'Nothing seen yet'}
                </p>
              </>
            )}
          </>
        )
        return (
          <li key={cam.id}>
            {unavailable ? (
              <div aria-disabled="true" className={`camera-card ${leafCardClass} block rounded-xl border border-stone-200 bg-stone-100 p-4 opacity-60`}>
                {body}
              </div>
            ) : (
              <a
                href={cameraHref(cam.id)}
                className={`camera-card ${leafCardClass} block rounded-xl border border-stone-200 bg-white p-4 shadow-sm hover:border-emerald-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500`}
              >
                {body}
              </a>
            )}
          </li>
        )
      })}
    </ul>
  )
}
