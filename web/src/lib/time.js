export function timeAgo(iso) {
  const secs = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (secs < 60) return 'just now'
  if (secs < 3600) return `${Math.floor(secs / 60)} min ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)} hr ago`
  return `${Math.floor(secs / 86400)} d ago`
}

// "tomorrow" (or a weekday name further out) when a time falls on a later calendar day than `now`
// in the viewer's local time, else null. Compares calendar days, not 24-hour spans, so 11 PM -> 1 AM counts.
export function dayTag(iso, now = Date.now()) {
  const day = (t) => {
    const d = new Date(t)
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  }
  const diff = Math.round((day(iso) - day(now)) / 86400000)
  if (diff <= 0) return null
  return diff === 1 ? 'tomorrow' : new Date(iso).toLocaleDateString([], { weekday: 'long' })
}
