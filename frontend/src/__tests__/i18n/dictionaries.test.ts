import { describe, it, expect } from 'vitest'
import { en } from '../../i18n/en'
import { vi } from '../../i18n/vi'

describe('translation dictionaries', () => {
  it('en and vi define exactly the same set of keys', () => {
    const enKeys = Object.keys(en).sort()
    const viKeys = Object.keys(vi).sort()
    expect(viKeys).toEqual(enKeys)
  })

  it('no translation value is an empty string', () => {
    for (const [key, value] of Object.entries(vi)) {
      expect(value, `vi.${key} should not be empty`).not.toBe('')
    }
  })
})
