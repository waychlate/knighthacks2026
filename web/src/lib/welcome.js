// Welcome screen is shown once per browser session, and only if the visit starts on the globe.
const KEY = 'envision-welcome-seen'
export const welcomeSeen = () => {
  try { return sessionStorage.getItem(KEY) === '1' } catch { return false }
}
export const markWelcomeSeen = () => {
  try { sessionStorage.setItem(KEY, '1') } catch { /* private mode: it just shows again */ }
}
