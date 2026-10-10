import { describe, expect, it } from 'vitest'
import { MAX_BODY, validateMessage } from './moderation'

const ok = (name, body, opts) => validateMessage(name, body, { lastSentAt: 0, now: 10_000, ...opts })

describe('validateMessage', () => {
  it('accepts a normal message and trims it', () => {
    expect(ok('  Sam ', '  saw an elk!  ')).toEqual({ ok: true, name: 'Sam', body: 'saw an elk!' })
  })
  it('rejects empty name, empty text and over-length text', () => {
    expect(ok('', 'hi').ok).toBe(false)
    expect(ok('Sam', '   ').ok).toBe(false)
    expect(ok('Sam', 'x'.repeat(MAX_BODY)).ok).toBe(true)
    expect(ok('Sam', 'x'.repeat(MAX_BODY + 1)).ok).toBe(false)
  })
  it('blocks listed words even with punctuation or spacing tricks', () => {
    expect(ok('Sam', 'what the f.u.c.k').ok).toBe(false)
    expect(ok('Sam', 'SHIT').ok).toBe(false)
    expect(ok('shit', 'hello').ok).toBe(false)
    expect(ok('Sam', 'Scunthorpe has elk').ok).toBe(true)
  })
  it('rate limits per sender', () => {
    expect(ok('Sam', 'hi', { lastSentAt: 9_000 }).ok).toBe(false)
    expect(ok('Sam', 'hi', { lastSentAt: 7_000 }).ok).toBe(true)
  })
})
