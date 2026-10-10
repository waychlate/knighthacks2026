import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { byCamera, byHour, bySpecies } from '../lib/analytics'

const COLOR = '#059669' // emerald-600

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

export default function AnalyticsPage({ sightings, loading, mode }) {
  const hours = useMemo(() => byHour(sightings), [sightings])
  const species = useMemo(() => bySpecies(sightings), [sightings])
  const cameras = useMemo(() => byCamera(sightings), [sightings])

  if (loading) return <p className="text-stone-500">Loading…</p>
  if (sightings.length === 0) {
    return (
      <p className="text-stone-500">
        {mode === 'live' ? 'No live sightings yet. Switch to Demo to see charts from recorded clips.' : 'No sightings to chart yet.'}
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-stone-500">
        {sightings.length} {mode === 'live' ? 'live' : 'demo'} sightings. Times are in your local time zone.
      </p>
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
      </Card>
      <Card title="Sightings by species">
        <Horizontal data={species} />
      </Card>
      <Card title="Sightings by camera">
        <Horizontal data={cameras} />
      </Card>
    </div>
  )
}
