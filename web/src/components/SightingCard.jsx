function timeAgo(iso) {
  const secs = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (secs < 60) return 'just now'
  if (secs < 3600) return `${Math.floor(secs / 60)} min ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)} hr ago`
  return `${Math.floor(secs / 86400)} d ago`
}

export default function SightingCard({ sighting }) {
  const { species, camera, seen_at, confidence, snapshot_url } = sighting
  const local = new Date(seen_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })

  return (
    <li className="flex items-center gap-4 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      {snapshot_url ? (
        <img src={snapshot_url} alt={species.common_name} className="h-16 w-16 rounded-lg object-cover" />
      ) : (
        <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-emerald-100 text-2xl" aria-hidden>
          🐾
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-stone-900">{species.common_name}</p>
        <p className="truncate text-sm italic text-stone-500">{species.scientific_name}</p>
        <p className="truncate text-sm text-stone-600">
          📷 {camera.name}
          {camera.location ? ` · ${camera.location}` : ''}
        </p>
      </div>
      <div className="shrink-0 text-right text-sm">
        <p className="font-medium text-stone-800">{timeAgo(seen_at)}</p>
        <p className="text-stone-500">{local}</p>
        <p className="text-xs text-stone-400">{Math.round(confidence * 100)}% sure</p>
      </div>
    </li>
  )
}
