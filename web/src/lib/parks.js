// Parks shown on the globe. Only Yellowstone has cameras and data; Katmai is a placeholder marker.
export const PARKS = [
  { slug: 'yellowstone', name: 'Yellowstone National Park', region: 'Wyoming, USA', lat: 44.6, lng: -110.5, active: true },
  { slug: 'katmai', name: 'Katmai National Park', region: 'Alaska, USA', lat: 58.5, lng: -155.0, active: false },
]

export const getPark = (slug) => PARKS.find((p) => p.slug === slug)

// Sightings today (local time) at the park's cameras.
export function sightingsToday(slug, sightings, cameras) {
  const ids = new Set(cameras.filter((c) => c.park === slug).map((c) => c.id))
  const midnight = new Date().setHours(0, 0, 0, 0)
  return sightings.filter((s) => ids.has(s.camera.id) && new Date(s.seen_at).getTime() >= midnight).length
}
