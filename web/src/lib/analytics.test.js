import { describe, expect, it } from 'vitest'
import { byCamera, byHour, bySpecies, hourLabel } from './analytics'

const mk = (species, camera, iso) => ({ species: { common_name: species }, camera: { name: camera }, seen_at: iso })
const rows = [
  mk('Elk', 'A', '2026-10-10T12:00:00'),
  mk('Elk', 'B', '2026-10-10T12:30:00'),
  mk('Bison', 'A', '2026-10-10T18:00:00'),
]

describe('analytics', () => {
  it('counts by species and camera, most common first', () => {
    expect(bySpecies(rows)).toEqual([{ name: 'Elk', count: 2 }, { name: 'Bison', count: 1 }])
    expect(byCamera(rows)).toEqual([{ name: 'A', count: 2 }, { name: 'B', count: 1 }])
  })
  it('buckets by local hour into 24 slots', () => {
    const h = byHour(rows) // timestamps without Z are local, so hours are stable across time zones
    expect(h).toHaveLength(24)
    expect(h[12].count).toBe(2)
    expect(h[18].count).toBe(1)
    expect(h.reduce((n, x) => n + x.count, 0)).toBe(3)
  })
  it('handles an empty list', () => {
    expect(bySpecies([])).toEqual([])
    expect(byHour([]).every((x) => x.count === 0)).toBe(true)
  })
  it('labels hours', () => {
    expect([0, 6, 12, 13, 23].map(hourLabel)).toEqual(['12a', '6a', '12p', '1p', '11p'])
  })
})
