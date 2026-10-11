import { useEffect, useRef } from 'react'
import { getDev } from '../lib/settings'
import { cameraHref } from '../lib/useRoute'
import Comments from './Comments'

const MODELS = 'YOLO (Ultralytics) + BioCLIP (Hugging Face)'

// Click-to-enlarge overlay for one sighting: the full frame, details, comments. Dev mode swaps in the frame with the box drawn and shows the detector numbers.
export default function SightingDialog({ sighting, onClose }) {
  const { id, species, camera, seen_at, confidence, snapshot_url, frame_url, annotated_url, bbox, yolo_score } = sighting
  const dev = getDev()
  const image = (dev && annotated_url) || frame_url || snapshot_url
  const closeBtn = useRef(null)
  useEffect(() => {
    closeBtn.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4" onClick={(e) => { e.stopPropagation(); onClose() }}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${species.common_name} sighting`}
        className="max-h-full w-full max-w-2xl space-y-3 overflow-y-auto rounded-2xl bg-stone-50 p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-xl font-bold text-stone-900">{species.common_name}</h2>
            <p className="truncate text-sm italic text-stone-500">{species.scientific_name}</p>
          </div>
          <button ref={closeBtn} type="button" onClick={onClose} aria-label="Close sighting" className="rounded-lg px-2 py-1 text-xl leading-none text-stone-600 hover:bg-stone-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500">×</button>
        </div>

        {image && <img src={image} alt={`${species.common_name} seen by ${camera.name}`} className="w-full rounded-xl bg-stone-200" />}

        <p className="text-sm text-stone-600">
          <a href={cameraHref(camera.id)} className="hover:text-emerald-700 hover:underline">📷 {camera.name}</a>
          {camera.location ? ` · ${camera.location}` : ''} · {new Date(seen_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
        </p>

        {dev && (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 rounded-xl border border-stone-200 bg-white p-3 text-sm">
            <dt className="text-stone-500">Detector score (YOLO)</dt>
            <dd className="font-mono text-stone-800">{yolo_score != null ? yolo_score.toFixed(2) : 'n/a'}</dd>
            <dt className="text-stone-500">Species confidence</dt>
            <dd className="font-mono text-stone-800">{Math.round(confidence * 100)}%</dd>
            <dt className="text-stone-500">Box (x1, y1, x2, y2)</dt>
            <dd className="font-mono text-stone-800">{bbox ? bbox.join(', ') : 'n/a'}</dd>
            <dt className="text-stone-500">Models</dt>
            <dd className="text-stone-800">{MODELS}</dd>
          </dl>
        )}

        <Comments sightingId={id} />
      </div>
    </div>
  )
}
