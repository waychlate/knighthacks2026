import { describe, expect, it } from 'vitest'
import { filterByMode, kindForMode, liveImageUrl, readMode, saveMode } from './live'
import { bearSeasonNote, hasLiveFeed } from './cameraConfig'

const rows = [{ id: 1, source_kind: 'live' }, { id: 2, source_kind: 'replay' }, { id: 3 }]

describe('mode filtering', () => {
  it('maps modes to source kinds', () => {
    expect(kindForMode('live')).toBe('live')
    expect(kindForMode('demo')).toBe('replay')
  })
  it('live mode shows only live rows', () => {
    expect(filterByMode(rows, 'live').map((r) => r.id)).toEqual([1])
  })
  it('demo mode shows replay rows, treating a missing source_kind as replay', () => {
    expect(filterByMode(rows, 'demo').map((r) => r.id)).toEqual([2, 3])
  })
})

describe('liveImageUrl', () => {
  it('adds a cache-busting query that changes with time', () => {
    const a = liveImageUrl('https://x/cam.jpg', 1_000_000)
    expect(a).toBe('https://x/cam.jpg?t=1000')
    expect(liveImageUrl('https://x/cam.jpg', 2_000_000)).not.toBe(a)
    expect(liveImageUrl('https://x/cam.jpg?a=1', 1_000_000)).toBe('https://x/cam.jpg?a=1&t=1000')
  })
})

describe('mode storage', () => {
  it('defaults to demo, round-trips, and survives broken storage', () => {
    const mem = new Map()
    const ok = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, v) }
    expect(readMode(ok)).toBe('demo')
    saveMode(ok, 'live')
    expect(readMode(ok)).toBe('live')
    const broken = { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('blocked') } }
    expect(readMode(broken)).toBe('demo')
    expect(() => saveMode(broken, 'live')).not.toThrow()
    expect(readMode(undefined)).toBe('demo')
  })
})

describe('cameras', () => {
  it('only Electric Peak has a live feed', () => {
    expect(hasLiveFeed({ name: 'Electric Peak Cam' })).toBe(true)
    expect(hasLiveFeed({ name: 'Lamar Valley Demo Cam' })).toBe(false)
    expect(hasLiveFeed({ name: 'Brooks Falls Low Cam' })).toBe(true) // explore.org video
    expect(hasLiveFeed(undefined)).toBe(false)
  })
})

describe('bearSeasonNote', () => {
  it('is silent in season and warns outside it', () => {
    expect(bearSeasonNote(new Date(2026, 9, 10))).toBeNull() // Oct 10
    expect(bearSeasonNote(new Date(2026, 5, 15))).toBeNull() // Jun 15
    expect(bearSeasonNote(new Date(2026, 5, 14))).toMatch(/highlights/)
    expect(bearSeasonNote(new Date(2026, 10, 1))).toMatch(/highlights/) // Nov 1
  })
})
