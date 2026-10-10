import { useMemo, useState } from 'react'
import Filters from '../components/Filters'
import SightingList from '../components/SightingList'

export default function FeedPage({ sightings, cameras, loading }) {
  const [filters, setFilters] = useState({ speciesId: '', cameraId: '' })

  // Only offer species that actually appear in the log
  const species = useMemo(() => {
    const byId = new Map(sightings.map((s) => [s.species.id, s.species]))
    return [...byId.values()].sort((a, b) => a.common_name.localeCompare(b.common_name))
  }, [sightings])

  const visible = useMemo(
    () =>
      sightings.filter(
        (s) =>
          (!filters.speciesId || s.species.id === filters.speciesId) &&
          (!filters.cameraId || s.camera.id === filters.cameraId),
      ),
    [sightings, filters],
  )

  return (
    <>
      <Filters species={species} cameras={cameras} value={filters} onChange={setFilters} />
      <SightingList sightings={visible} loading={loading} emptyText="No sightings match these filters." />
    </>
  )
}
