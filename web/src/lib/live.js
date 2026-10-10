// Pure helpers for the Demo/Live mode. Kept free of React so they are easy to test.

export const MODES = ['demo', 'live']

// Live sightings are source_kind 'live'; demo mode shows 'replay' (recorded clips and seed data).
// Rows from an older schema without source_kind count as 'replay'.
export const kindForMode = (mode) => (mode === 'live' ? 'live' : 'replay')

export function filterByMode(sightings, mode) {
  const kind = kindForMode(mode)
  return sightings.filter((s) => (s.source_kind ?? 'replay') === kind)
}

// The NPS still refreshes every 30-60 s; a changing query string defeats browser/CDN caching.
export function liveImageUrl(url, now = Date.now()) {
  return `${url}${url.includes('?') ? '&' : '?'}t=${Math.floor(now / 1000)}`
}

export const LIVE_REFRESH_MS = 60_000

export function readMode(storage) {
  try {
    const v = storage?.getItem('mode')
    return MODES.includes(v) ? v : 'demo'
  } catch {
    return 'demo'
  }
}

export function saveMode(storage, mode) {
  try {
    storage?.setItem('mode', mode)
  } catch {
    // private window / blocked storage: the toggle still works for this visit
  }
}
