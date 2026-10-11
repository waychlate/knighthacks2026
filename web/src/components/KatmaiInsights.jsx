import { useEffect, useState } from 'react'

const number = new Intl.NumberFormat()

function Metric({ label, value, note }) {
  return (
    <div className="katmai-metric rounded-xl border border-sky-100 bg-sky-50/70 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-sky-800">{label}</p>
      <p className="mt-1 text-2xl font-bold text-stone-900">{number.format(value)}</p>
      <p className="mt-1 text-xs text-stone-500">{note}</p>
    </div>
  )
}

function Insight({ insight }) {
  return (
    <article className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-stone-600">{insight.title}</p>
      <p className="insight-value mt-1 text-2xl font-bold text-sky-800">{insight.value}</p>
      <p className="mt-2 text-sm leading-6 text-stone-700">{insight.detail}</p>
      <p className="mt-3 border-l-2 border-amber-400 pl-3 text-xs leading-5 text-stone-500">{insight.caveat}</p>
    </article>
  )
}

function Chart({ chart, wide = false }) {
  return (
    <figure className={`overflow-hidden rounded-xl border border-stone-200 bg-white shadow-sm ${wide ? 'lg:col-span-2' : ''}`}>
      <div className="border-b border-stone-200 px-4 py-3">
        <h4 className="font-semibold text-stone-900">{chart.title}</h4>
      </div>
      <a href={chart.src} target="_blank" rel="noreferrer" className="block min-h-0 p-3" aria-label={`Open full-size chart: ${chart.title}`}>
        <img src={chart.src} alt={chart.title} loading="lazy" className="h-auto w-full rounded-lg bg-white" />
      </a>
    </figure>
  )
}

export default function KatmaiInsights() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch('/katmai/insights/insights.json')
      .then((response) => {
        if (!response.ok) throw new Error(`Insights request failed (${response.status})`)
        return response.json()
      })
      .then((json) => {
        if (!cancelled) setData(json)
      })
      .catch((reason) => {
        if (!cancelled) setError(reason.message)
      })
    return () => { cancelled = true }
  }, [])

  if (error) {
    return <p role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Historical Katmai insights are temporarily unavailable. {error}</p>
  }
  if (!data) {
    return <div className="skeleton h-48" role="status" aria-label="Loading Katmai research insights" />
  }

  const generated = new Date(data.generated_at).toLocaleDateString([], {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  return (
    <section aria-labelledby="katmai-research-title" className="katmai-insights space-y-4">
      <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-sky-950 via-sky-900 to-cyan-800 p-5 text-white shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">Data science · historical context</p>
            <h3 id="katmai-research-title" className="mt-2 text-2xl font-bold">Katmai wildlife patterns</h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-sky-100">
              Camera detections are compared with public brown-bear observations, weather, and calculated daylight to describe when and where records appeared.
            </p>
          </div>
          <span className="w-fit rounded-full bg-white/10 px-3 py-1 text-xs text-sky-100">Updated {generated}</span>
        </div>
        <p className="mt-4 rounded-lg border border-amber-200/40 bg-amber-100/10 px-3 py-2 text-xs leading-5 text-amber-50">
          These are descriptive patterns, not population estimates or guarantees that an animal will appear.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label="Research sample sizes">
        <Metric label="Camera frames" value={data.summary.camera_frames} note="Frames reviewed across three cameras" />
        <Metric label="Accepted boxes" value={data.summary.accepted_detection_boxes} note="Model detections after review thresholds" />
        <Metric label="Public bear records" value={data.summary.public_bear_records} note="GBIF regional occurrence records" />
        <Metric label="Weather days" value={data.summary.weather_days} note="NASA POWER historical daily records" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {data.insights.map((insight) => <Insight key={insight.id} insight={insight} />)}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {data.charts.map((chart, index) => <Chart key={chart.id} chart={chart} wide={index === data.charts.length - 1 && data.charts.length % 2 === 1} />)}
      </div>

      <details className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
        <summary className="cursor-pointer font-semibold text-stone-900">Sources and research limitations</summary>
        <div className="mt-4 grid gap-5 lg:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold text-stone-800">Sources</h4>
            <ul className="mt-2 space-y-2 text-sm">
              {data.sources.map((source) => (
                <li key={source.name}>
                  <a href={source.url} target="_blank" rel="noreferrer" className="katmai-source-link text-sky-700 underline decoration-sky-300 underline-offset-2 hover:text-sky-900">{source.name}</a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-stone-800">How to read these results</h4>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-5 text-stone-600">
              {data.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
            </ul>
          </div>
        </div>
      </details>
    </section>
  )
}
