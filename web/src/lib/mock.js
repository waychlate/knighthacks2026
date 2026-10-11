// Mock data so the UI works before Supabase / the worker exist. ALL of it is made up.
// Shape matches a `sightings` row joined with its species and camera (see supabase/schema.sql).
// Camera names match supabase/seed.sql; only "Electric Peak Cam" has a real live image (cameraConfig.js).

export const MOCK_CAMERAS = [
  { id: 'cam-1', name: 'Electric Peak Cam', location: 'North Entrance, Gardiner', park: 'yellowstone' },
  { id: 'cam-2', name: 'Lamar Valley Demo Cam', location: 'Lamar Valley (demo camera)', park: 'yellowstone' },
  { id: 'cam-3', name: 'Hayden Valley Demo Cam', location: 'Hayden Valley (demo camera)', park: 'yellowstone' },
  { id: 'cam-4', name: 'Brooks Falls Bearcam', location: 'Brooks Falls, Katmai National Park', park: 'katmai' },
  { id: 'cam-5', name: 'Brooks Falls Low Cam', location: 'Brooks Falls (low camera)', park: 'katmai' },
  { id: 'cam-6', name: 'River Watch Cam', location: 'Brooks River', park: 'katmai' },
]

export const MOCK_SPECIES = [
  { id: 'sp-1', common_name: 'Elk', scientific_name: 'Cervus canadensis' },
  { id: 'sp-2', common_name: 'American bison', scientific_name: 'Bison bison' },
  { id: 'sp-3', common_name: 'Pronghorn', scientific_name: 'Antilocapra americana' },
  { id: 'sp-4', common_name: 'Coyote', scientific_name: 'Canis latrans' },
  { id: 'sp-5', common_name: 'Grizzly bear', scientific_name: 'Ursus arctos horribilis' },
  { id: 'sp-6', common_name: 'Bald eagle', scientific_name: 'Haliaeetus leucocephalus' },
]

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]

let counter = 0
// Mock sightings are demo/replay data, never 'live'.
export function makeMockSighting(seenAt = new Date()) {
  counter += 1
  return {
    id: `mock-${Date.now()}-${counter}`,
    seen_at: seenAt.toISOString(),
    confidence: Math.round((0.6 + Math.random() * 0.39) * 100) / 100,
    snapshot_url: null,
    source_kind: 'replay',
    species: pick(MOCK_SPECIES),
    camera: pick(MOCK_CAMERAS),
  }
}

export function makeMockHistory(n = 40) {
  const now = Date.now()
  return Array.from({ length: n }, (_, i) => makeMockSighting(new Date(now - (i + 1) * 37 * 60 * 1000)))
}

// Fallback sample predictions (same shape as a joined `predictions` row), relative to "now".
// usePredictions prefers /predictions.sample.json from the ML job when it exists.
export function makeMockPredictions() {
  const at = (mins) => new Date(Date.now() + mins * 60 * 1000).toISOString()
  return [
    { id: 'pred-1', predicted_for: at(25), probability: 0.34, species: MOCK_SPECIES[0], camera: MOCK_CAMERAS[0] },
    { id: 'pred-2', predicted_for: at(115), probability: 0.28, species: MOCK_SPECIES[1], camera: MOCK_CAMERAS[2] },
    { id: 'pred-3', predicted_for: at(240), probability: 0.19, species: MOCK_SPECIES[2], camera: null },
  ]
}

// Sample chat and comments (also made up), so the social UI is not empty on first load.
export function makeMockChat(park = 'yellowstone') {
  const ago = (m) => new Date(Date.now() - m * 60 * 1000).toISOString()
  return [
    { id: 'chat-1', park, display_name: 'ranger_rae (sample)', body: 'Sample chat: elk are usually out near Gardiner around sunrise.', created_at: ago(42) },
    { id: 'chat-2', park, display_name: 'trailmix (sample)', body: 'Sample chat: anyone seen the Lamar Valley bison today?', created_at: ago(15) },
  ]
}
