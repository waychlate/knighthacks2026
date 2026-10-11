import { useState } from 'react'
import { cameraHref } from '../lib/useRoute'
import { timeAgo } from '../lib/time'
import SightingDialog from './SightingDialog'

export default function SightingCard({ sighting }) {
  const { species, camera, seen_at, confidence, snapshot_url } = sighting
  const local = new Date(seen_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
  const [open, setOpen] = useState(false)

  return (
    <li onClick={(e) => !e.target.closest('a') && setOpen(true)} className="cursor-pointer rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-4">
        {snapshot_url ? (
          <img src={snapshot_url} alt={`${species.common_name} seen by ${camera.name}`} className="h-16 w-16 rounded-lg object-cover" />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-emerald-100 text-2xl" aria-hidden>
            🐾
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-stone-900">{species.common_name}</p>
          <p className="truncate text-sm italic text-stone-500">{species.scientific_name}</p>
          <a href={cameraHref(camera.id)} className="block truncate text-sm text-stone-600 hover:text-emerald-700 hover:underline">
            📷 {camera.name}
            {camera.location ? ` · ${camera.location}` : ''}
          </a>
        </div>
        <div className="shrink-0 text-right text-sm">
          <p className="font-medium text-stone-800">{timeAgo(seen_at)}</p>
          <p className="text-stone-500">{local}</p>
          <p className="text-xs text-stone-400">{Math.round(confidence * 100)}% sure</p>
        </div>
      </div>
      <button
        type="button"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
        className="mt-2 rounded text-sm text-emerald-700 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
      >
        💬 Details & comments
      </button>
      {open && <SightingDialog sighting={sighting} onClose={() => setOpen(false)} />}
    </li>
  )
}
