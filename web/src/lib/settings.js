// Per-browser settings: the anonymous chat display name and the dev flag. Storage can be blocked, so every access is guarded.
import { cleanName } from './moderation'

const NAME_KEY = 'displayName'
const DEV_KEY = 'devMode'

const read = (key) => {
  try { return window.localStorage.getItem(key) } catch { return null }
}
const write = (key, value) => {
  try { window.localStorage.setItem(key, value) } catch { /* storage blocked: the setting just isn't remembered */ }
}

export const randomName = (rand = Math.random) => `Visitor ${1000 + Math.floor(rand() * 9000)}`

// The saved name, or a new "Visitor 1234" saved on first use so chatting never needs a trip to Settings.
export function getDisplayName() {
  const saved = cleanName(read(NAME_KEY))
  if (saved) return saved
  const name = randomName()
  write(NAME_KEY, name)
  return name
}

export function setDisplayName(name) {
  const clean = cleanName(name)
  if (clean) write(NAME_KEY, clean)
  return clean
}

export const getDev = () => read(DEV_KEY) === '1'
export const setDev = (on) => write(DEV_KEY, on ? '1' : '0')
