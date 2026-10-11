import { createPortal } from 'react-dom'
import { parkHref } from '../lib/useRoute'

const link = (active) =>
  `rounded-lg px-3 py-1.5 text-sm font-medium capitalize focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
    active ? 'bg-emerald-100 text-emerald-800' : 'text-stone-600 hover:bg-stone-100'
  }`

// Sightings and Predictions live on the Cameras page, so those routes highlight Cameras.
export const navTab = (tab) => (tab === 'sightings' || tab === 'predictions' ? 'cameras' : tab)

const openSettings = () => window.dispatchEvent(new Event('envision:open-settings'))

export default function Nav({ park, tab, limited = false }) {
  const current = navTab(tab)
  const icon = park === 'katmai' ? <span className="katmai-fish" aria-hidden>🐟</span> : <span className="yellowstone-bison" aria-hidden>🦬</span>
  const renderLink = (t) => (
    <a key={t} href={parkHref(park, t)} className={link(t === current)} aria-current={t === current ? 'page' : undefined}>
      {icon}
      {t}
    </a>
  )
  const item = (key, emoji, label) => (
    <a key={key} href={parkHref(park, key)} aria-current={key === current ? 'page' : undefined} className={`mobile-nav-item ${key === current ? 'is-active' : ''}`}>
      <span className="nav-icon" aria-hidden>{emoji}</span>
      {label}
    </a>
  )

  return (
    <>
      {!limited && (
        <div className="desktop-nav">
          <nav className="flex flex-wrap gap-1" aria-label="Primary park sections">
            {['cameras', 'analytics'].map(renderLink)}
          </nav>
        </div>
      )}
      {createPortal(
      <div className="mobile-nav">
        <nav aria-label="Park sections">
          {!limited && item('cameras', '📷', 'Cameras')}
          {item('chat', '💬', 'Chat')}
          <a href="#/" className="mobile-nav-item mobile-nav-globe" aria-label="Back to the globe">
            <span className="nav-icon" aria-hidden>🌍</span>
            Globe
          </a>
          {!limited && item('analytics', '📊', 'Analytics')}
          <button type="button" onClick={openSettings} className="mobile-nav-item">
            <span className="nav-icon" aria-hidden>⚙</span>
            Settings
          </button>
        </nav>
      </div>,
        document.body,
      )}
    </>
  )
}
