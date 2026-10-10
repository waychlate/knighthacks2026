import SightingCard from './SightingCard'

export default function SightingList({ sightings, loading, emptyText = 'No sightings match.' }) {
  if (loading) return <div className="space-y-3" aria-label="Loading sightings"><div className="skeleton h-24" /><div className="skeleton h-24" /><div className="skeleton h-24" /></div>
  if (sightings.length === 0) return <div className="empty-state" role="status"><span className="text-3xl" aria-hidden>◌</span><p>{emptyText}</p><p className="text-sm text-stone-500">Try changing the filters or check back after the cameras report in.</p></div>
  return (
    <ul className="space-y-3">
      {sightings.map((s) => (
        <SightingCard key={s.id} sighting={s} />
      ))}
    </ul>
  )
}
