import { useSyncExternalStore } from 'react'

// Demo-mode pins: placed by tapping the map. Kept in memory only (gone on reload), never sent to Supabase,
// shared between the globe and the park map. Flagged `sample` and `demo` so the UI labels them.
let pins = []
const subs = new Set()

export function addDemoPin({ lat, lng, species_name, note }) {
  const pin = { id: `demo-${Date.now()}`, lat, lng, species_name: species_name || null, note: note || null, created_at: new Date().toISOString(), sample: true, demo: true }
  pins = [pin, ...pins]
  subs.forEach((f) => f())
}

export const useDemoPins = () =>
  useSyncExternalStore((cb) => (subs.add(cb), () => subs.delete(cb)), () => pins)
