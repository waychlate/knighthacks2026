// Aggregations for the analytics page, computed from the loaded sightings.

const byCount = (a, b) => b.count - a.count || a.name.localeCompare(b.name)

function tally(sightings, keyOf) {
  const map = new Map()
  for (const s of sightings) {
    const name = keyOf(s)
    map.set(name, (map.get(name) ?? 0) + 1)
  }
  return [...map].map(([name, count]) => ({ name, count })).sort(byCount)
}

export const bySpecies = (sightings) => tally(sightings, (s) => s.species.common_name)
export const byCamera = (sightings) => tally(sightings, (s) => s.camera.name)

// 24 buckets, 0-23, in the viewer's local time (the stored timestamps are UTC).
export function byHour(sightings) {
  const counts = Array.from({ length: 24 }, (_, hour) => ({ hour, label: hourLabel(hour), count: 0 }))
  for (const s of sightings) counts[new Date(s.seen_at).getHours()].count += 1
  return counts
}

export const hourLabel = (h) => `${h % 12 === 0 ? 12 : h % 12}${h < 12 ? 'a' : 'p'}`
