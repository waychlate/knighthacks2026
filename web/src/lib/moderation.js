// Client-side checks for anonymous chat and comments. The database enforces the same length limits
// and a per-name rate limit (supabase/social.sql); this just gives instant feedback.

export const MAX_BODY = 280
export const MAX_NAME = 40
export const MIN_GAP_MS = 2000

// Deliberately short placeholder list; swap in a real one before a public launch.
const BLOCKED = ['fuck', 'shit', 'bitch', 'asshole', 'cunt', 'nigger', 'faggot']

// Whole-word match (so "Scunthorpe" is fine), plus runs of single letters joined ("f.u.c.k" -> "fuck").
function isBlocked(text) {
  const tokens = text.toLowerCase().split(/[^a-z]+/).filter(Boolean)
  const joined = []
  let run = ''
  for (const t of tokens) {
    if (t.length === 1) run += t
    else {
      if (run) joined.push(run)
      run = ''
      joined.push(t)
    }
  }
  if (run) joined.push(run)
  return joined.some((t) => BLOCKED.includes(t.replace(/(s|ing|ed)$/, '')) || BLOCKED.includes(t))
}

export const cleanName = (s) => (s ?? '').trim().replace(/\s+/g, ' ').slice(0, MAX_NAME)

export function validateMessage(name, body, { lastSentAt = 0, now = Date.now() } = {}) {
  const n = cleanName(name)
  const text = (body ?? '').trim()
  if (!n) return { ok: false, error: 'Pick a display name first.' }
  if (!text) return { ok: false, error: 'Write something first.' }
  if (text.length > MAX_BODY) return { ok: false, error: `Keep it under ${MAX_BODY} characters.` }
  if (isBlocked(text) || isBlocked(n)) {
    return { ok: false, error: 'Please keep it friendly.' }
  }
  if (now - lastSentAt < MIN_GAP_MS) return { ok: false, error: 'Slow down a little.' }
  return { ok: true, name: n, body: text }
}
