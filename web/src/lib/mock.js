// Mock data so the UI works before Supabase / the worker exist.
// Shape matches a `sightings` row joined with its species and camera.

export const MOCK_CAMERAS = [
  { id: 'cam-1', name: 'River Overlook', location: 'North trail' },
  { id: 'cam-2', name: 'Meadow Cam', location: 'East meadow' },
  { id: 'cam-3', name: 'Pond Cam', location: 'South pond' },
]

export const MOCK_SPECIES = [
  { id: 'sp-1', common_name: 'Northern Cardinal', scientific_name: 'Cardinalis cardinalis' },
  { id: 'sp-2', common_name: 'White-tailed Deer', scientific_name: 'Odocoileus virginianus' },
  { id: 'sp-3', common_name: 'Great Blue Heron', scientific_name: 'Ardea herodias' },
  { id: 'sp-4', common_name: 'Eastern Gray Squirrel', scientific_name: 'Sciurus carolinensis' },
  { id: 'sp-5', common_name: 'American Black Bear', scientific_name: 'Ursus americanus' },
]

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]

let counter = 0
export function makeMockSighting(seenAt = new Date()) {
  counter += 1
  return {
    id: `mock-${Date.now()}-${counter}`,
    seen_at: seenAt.toISOString(),
    confidence: Math.round((0.6 + Math.random() * 0.39) * 100) / 100,
    snapshot_url: null,
    species: pick(MOCK_SPECIES),
    camera: pick(MOCK_CAMERAS),
  }
}

export function makeMockHistory(n = 12) {
  const now = Date.now()
  return Array.from({ length: n }, (_, i) =>
    makeMockSighting(new Date(now - (i + 1) * 7 * 60 * 1000)),
  )
}

// Sample predictions (same shape as a joined `predictions` row), relative to "now".
export function makeMockPredictions() {
  const at = (mins) => new Date(Date.now() + mins * 60 * 1000).toISOString()
  return [
    { id: 'pred-1', predicted_for: at(25), probability: 0.78, species: MOCK_SPECIES[2], camera: MOCK_CAMERAS[2] },
    { id: 'pred-2', predicted_for: at(115), probability: 0.64, species: MOCK_SPECIES[1], camera: MOCK_CAMERAS[1] },
    { id: 'pred-3', predicted_for: at(240), probability: 0.52, species: MOCK_SPECIES[0], camera: null },
  ]
}
