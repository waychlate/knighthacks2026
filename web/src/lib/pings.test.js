import { describe, expect, it } from 'vitest'
import { latestSighting } from './parks'
import { cooldownLeftMs, speciesFor, distanceKm, makeSamplePings, markPinged, nearestPark, recent, roundCoord, toGeoJSON } from './pings'

const store = () => {
  const m = {}
  return { getItem: (k) => m[k] ?? null, setItem: (k, v) => (m[k] = v) }
}

describe('pings', () => {
  it('rounds to about 500 m', () => {
    expect(roundCoord(28.54321)).toBeCloseTo(28.545, 6)
    expect(Math.abs(roundCoord(-81.3781) - -81.3781)).toBeLessThanOrEqual(0.0025 + 1e-9)
  })
  it('measures distance', () => {
    expect(distanceKm(0, 0, 0, 1)).toBeCloseTo(111.2, 0)
  })
  it('finds the park within its radius, else null', () => {
    expect(nearestPark(44.6, -110.5)).toBe('yellowstone')
    expect(nearestPark(58.5, -155.2)).toBe('katmai')
    expect(nearestPark(44.97, -110.69)).toBe('yellowstone')
    expect(nearestPark(28.54, -81.38)).toBeNull()
  })
  it('drops pings older than 24 h', () => {
    const now = Date.now()
    const old = new Date(now - 25 * 3600e3).toISOString()
    const fresh = new Date(now - 3600e3).toISOString()
    expect(recent([{ created_at: old }, { created_at: fresh }], now)).toHaveLength(1)
  })
  it('enforces a 5 minute cooldown', () => {
    const s = store()
    expect(cooldownLeftMs(s)).toBe(0)
    markPinged(s, 1000)
    expect(cooldownLeftMs(s, 1000 + 60e3)).toBe(4 * 60e3)
    expect(cooldownLeftMs(s, 1000 + 6 * 60e3)).toBe(0)
  })
  it('flags sample pings and colours near/elsewhere', () => {
    const f = toGeoJSON(makeSamplePings()).features
    expect(f.every((x) => x.properties.sample)).toBe(true)
    expect(f.some((x) => x.properties.near)).toBe(true)
    expect(f.some((x) => !x.properties.near)).toBe(true)
  })
  it('finds the newest sighting at a park', () => {
    const cams = [{ id: 'a', park: 'yellowstone' }, { id: 'b', park: 'katmai' }]
    const list = [{ id: 1, camera: { id: 'b' } }, { id: 2, camera: { id: 'a' } }, { id: 3, camera: { id: 'a' } }]
    expect(latestSighting('yellowstone', list, cams).id).toBe(2)
    expect(latestSighting('nowhere', list, cams)).toBeUndefined()
  })
  it('offers only the species of the park you are in', () => {
    expect(speciesFor(44.6, -110.5)).toContain('American bison')
    expect(speciesFor(44.6, -110.5)).not.toContain('Brown bear')
    expect(speciesFor(58.5, -155.1)).toContain('Brown bear')
    expect(speciesFor(58.5, -155.1)).not.toContain('American bison')
    expect(speciesFor(28.54, -81.38)).toBeNull()
  })
})
