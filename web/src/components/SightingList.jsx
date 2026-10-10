import SightingCard from './SightingCard'

export default function SightingList({ sightings, loading, emptyText = 'No sightings match.' }) {
  if (loading) return <p className="text-stone-500">Loading…</p>
  if (sightings.length === 0) return <p className="text-stone-500">{emptyText}</p>
  return (
    <ul className="space-y-3">
      {sightings.map((s) => (
        <SightingCard key={s.id} sighting={s} />
      ))}
    </ul>
  )
}
