import { PARKS } from './parks'

// User pings: "I saw something here". User-reported, anonymous, never mixed into `sightings`.
// Pure helpers live here so they are easy to test; the React hook is in usePings.js.

export const PING_TTL_MS = 24 * 60 * 60 * 1000
export const PING_COOLDOWN_MS = 5 * 60 * 1000
export const NOTE_MAX = 140
const ROUND_STEP = 0.005 // about 500 m; supabase/pings.sql rounds the same way

// Candidate species for the picker: the Yellowstone list in worker/species.json (the only park with data).
export const PING_SPECIES = [
  'Elk', 'American bison', 'Pronghorn', 'Mule deer', 'Coyote', 'Gray wolf', 'Grizzly bear',
  'American black bear', 'Bighorn sheep', 'Moose', 'Bald eagle', 'Trumpeter swan', 'Sandhill crane', 'Red fox',
]

export const roundCoord = (x) => Math.round(x / ROUND_STEP) * ROUND_STEP

export function distanceKm(lat1, lng1, lat2, lng2) {
  const rad = Math.PI / 180
  const a =
    Math.sin(((lat2 - lat1) * rad) / 2) ** 2 +
    Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(((lng2 - lng1) * rad) / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(a))
}

// Slug of the park whose radius covers the point, or null ("elsewhere").
export function nearestPark(lat, lng) {
  let best = null
  for (const p of PARKS) {
    const d = distanceKm(lat, lng, p.lat, p.lng)
    if (d <= p.radiusKm && (!best || d < best.d)) best = { slug: p.slug, d }
  }
  return best?.slug ?? null
}

// Pings from the last 24 hours only.
export const recent = (pings, now = Date.now()) =>
  pings.filter((p) => now - new Date(p.created_at).getTime() < PING_TTL_MS)

// GeoJSON for the map. `near` colours the dot (in a park or elsewhere).
export function toGeoJSON(pings) {
  return {
    type: 'FeatureCollection',
    features: pings.map((p) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
      properties: { id: p.id, near: nearestPark(p.lat, p.lng) !== null, species: p.species_name ?? '', note: p.note ?? '', created_at: p.created_at, sample: Boolean(p.sample) },
    })),
  }
}

// One ping per device per 5 minutes. Client-side only: it stops accidents, not a determined person.
export function cooldownLeftMs(storage, now = Date.now()) {
  try {
    const last = Number(storage?.getItem('lastPing'))
    return Math.max(0, PING_COOLDOWN_MS - (now - last))
  } catch {
    return 0
  }
}

export function markPinged(storage, now = Date.now()) {
  try {
    storage?.setItem('lastPing', String(now))
  } catch {
    /* private mode: no limit */
  }
}

// Made-up pings for Demo mode only. Every one is flagged `sample`, shown as "sample" in the UI.
export function makeSamplePings(now = Date.now()) {
  const ago = (m) => new Date(now - m * 60 * 1000).toISOString()
  const mk = (i, lat, lng, species_name, note, min) => ({ id: `sample-${i}`, lat, lng, species_name, note, created_at: ago(min), sample: true })
  return [
    mk(1, 44.97, -110.69, 'Elk', 'Sample ping: a herd by the road.', 12),
    mk(2, 44.66, -111.1, 'American bison', 'Sample ping: bison crossing.', 35),
    mk(3, 44.92, -110.42, 'Coyote', 'Sample ping', 70),
    mk(4, 44.62, -110.5, 'Grizzly bear', 'Sample ping: far off, with binoculars.', 150),
    mk(5, 44.75, -110.55, 'Moose', '', 300),
    mk(6, 58.55, -155.1, 'Brown bear', 'Sample ping: fishing at the falls.', 20),
    mk(7, 58.48, -154.95, 'Brown bear', 'Sample ping', 90),
    mk(8, 28.54, -81.38, '', 'Sample ping: backyard heron (elsewhere).', 45),
  ]
}
