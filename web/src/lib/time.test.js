import { describe, expect, it } from 'vitest'
import { dayTag } from './time'

// Local-time constructors keep these tests independent of the machine's time zone.
const at = (d, h, m = 0) => new Date(2026, 9, d, h, m).toISOString()
const now = new Date(2026, 9, 10, 22, 30).getTime()

describe('dayTag', () => {
  it('is null for later today and for the past', () => {
    expect(dayTag(at(10, 23, 59), now)).toBeNull()
    expect(dayTag(at(10, 1), now)).toBeNull()
    expect(dayTag(at(9, 8), now)).toBeNull()
  })
  it('says tomorrow for the next calendar day, even if under 24 hours away', () => {
    expect(dayTag(at(11, 0, 5), now)).toBe('tomorrow') // 1h35m from now, but tomorrow
    expect(dayTag(at(11, 10, 41), now)).toBe('tomorrow')
    expect(dayTag(at(11, 23, 59), now)).toBe('tomorrow')
  })
  it('uses the weekday name beyond tomorrow', () => {
    expect(dayTag(at(13, 9), now)).toMatch(/^[A-Za-z]+$/)
    expect(dayTag(at(13, 9), now)).not.toBe('tomorrow')
  })
})
