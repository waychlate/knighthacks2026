import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import KatmaiInsights from '../components/KatmaiInsights'
import { byCamera, byHour, bySpecies } from '../lib/analytics'

const COLOR = '#059669'

function Card({ title, children }) {
  return (
    <section aria-label={title} className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-semibold text-stone-900">{title}</h3>
      {children}
    </section>
  )
}

function Horizontal({ data }) {
  return (
    <div role="img" aria-label={data.map((d) => `${d.name}: ${d.count}`).join(', ')} style={{ height: Math.max(120, data.length * 34) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid horizontal={false} stroke="#e7e5e4" />
          <XAxis type="number" allowDecimals={false} />
          <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="count" name="Sightings" fill={COLOR} radius={[0, 4, 4, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function FeedAnalytics({ sightings, mode, hours, species, cameras }) {
  if (sightings.length === 0) {
    return (
      <section aria-labelledby="feed-analytics-title" className="rounded-xl border border-dashed border-stone-300 bg-white p-5">
        <h3 id="feed-analytics-title" className="font-semibold text-stone-900">Sighting feed analytics</h3>
        <p className="mt-1 text-sm text-stone-500">
          {mode === 'live' ? 'No live sightings yet. New model detections will appear here automatically.' : 'No demo sightings are available to chart.'}
        </p>
      </section>
    )
  }

  return (
    <section aria-labelledby="feed-analytics-title" className="space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-stone-500">Current app data</p>
        <h3 id="feed-analytics-title" className="mt-1 text-xl font-bold text-stone-900">Sighting feed analytics</h3>
        <p className="mt-1 text-sm text-stone-500">
          {sightings.length} {mode === 'live' ? 'live' : 'demo'} sightings. Times are in your local time zone.
        </p>
      </div>
      <Card title="Sightings by hour of day">
        <div role="img" aria-label={`Sightings per hour. Busiest hour: ${hours.reduce((a, b) => (b.count > a.count ? b : a)).label}`} style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hours} margin={{ left: -16, right: 8 }}>
              <CartesianGrid vertical={false} stroke="#e7e5e4" />
              <XAxis dataKey="label" interval={1} tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Sightings" fill={COLOR} radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="sr-only">Sightings by hour: {hours.map((item) => `${item.label}, ${item.count}`).join('; ')}.</p>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Sightings by species">
          <Horizontal data={species} />
          <p className="sr-only">Sightings by species: {species.map((item) => `${item.name}, ${item.count}`).join('; ')}.</p>
        </Card>
        <Card title="Sightings by camera">
          <Horizontal data={cameras} />
          <p className="sr-only">Sightings by camera: {cameras.map((item) => `${item.name}, ${item.count}`).join('; ')}.</p>
        </Card>
      </div>
    </section>
  )
}

export default function AnalyticsPage({ sightings, loading, mode, park }) {
  const hours = useMemo(() => byHour(sightings), [sightings])
  const species = useMemo(() => bySpecies(sightings), [sightings])
  const cameras = useMemo(() => byCamera(sightings), [sightings])

  if (loading) return <p className="text-stone-500">Loading…</p>

  return (
    <div className="space-y-8">
      {park === 'katmai' && <KatmaiInsights />}
      <FeedAnalytics sightings={sightings} mode={mode} hours={hours} species={species} cameras={cameras} />
    </div>
  )
}
