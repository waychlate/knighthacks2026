import { cameraHref } from '../lib/useRoute'
import { dayTag } from '../lib/time'

const clock = (iso) => new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })

// Clock time, with "tomorrow" (or a weekday) when the model expects it on a later day.
function When({ iso }) {
  const tag = dayTag(iso)
  return (
    <>
      <strong>{clock(iso)}</strong>
      {tag && <span className="ml-1 rounded-full bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800">{tag}</span>}
    </>
  )
}

function inText(iso) {
  const mins = Math.round((new Date(iso).getTime() - Date.now()) / 60000)
  if (mins <= 0) return 'now'
  if (mins < 60) return `in ${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m ? `in ${h} hr ${m} min` : `in ${h} hr`
}

function Where({ camera }) {
  if (!camera) return <span>anywhere in the park</span>
  return (
    <a href={cameraHref(camera.id)} className="hover:underline">
      near {camera.name}
    </a>
  )
}

export default function PredictionCard({ predictions, loading, usingMock }) {
  if (loading) return null
  const [next, ...later] = predictions

  return (
    <section
      aria-label="Sighting predictions"
      className="mb-6 rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5 shadow-sm"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">🔮 Coming up</h2>
        {usingMock && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">sample predictions</span>
        )}
      </div>

      {!next ? (
        <p className="text-sm text-stone-500">Not enough data yet to predict what will show up. Check back soon.</p>
      ) : (
        <>
          <p className="text-lg text-stone-900">
            Predicting a <strong>{next.species.common_name}</strong> around <When iso={next.predicted_for} />
          </p>
          <p className="mt-1 text-sm text-stone-600">
            <Where camera={next.camera} /> · {inText(next.predicted_for)} · {Math.round(next.probability * 100)}% likely
          </p>

          {later.length > 0 && (
            <ul className="mt-4 space-y-1.5 border-t border-emerald-100 pt-3 text-sm text-stone-600">
              {later.map((p) => (
                <li key={p.id} className="flex flex-wrap justify-between gap-x-3">
                  <span>
                    <strong className="font-medium text-stone-800">{p.species.common_name}</strong> around <When iso={p.predicted_for} />
                  </span>
                  <span className="text-stone-500">{Math.round(p.probability * 100)}% likely</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  )
}
