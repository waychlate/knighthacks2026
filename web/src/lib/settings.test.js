import { describe, expect, it } from 'vitest'
import { randomName } from './settings'

describe('randomName', () => {
  it('makes a 4-digit Visitor name at both ends of the range', () => {
    expect(randomName(() => 0)).toBe('Visitor 1000')
    expect(randomName(() => 0.9999999)).toBe('Visitor 9999')
  })
})
