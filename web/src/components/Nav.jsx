import { parkHref, TABS } from '../lib/useRoute'

const link = (active) =>
  `rounded-lg px-3 py-1.5 text-sm font-medium capitalize focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
    active ? 'bg-emerald-100 text-emerald-800' : 'text-stone-600 hover:bg-stone-100'
  }`

export default function Nav({ park, tab }) {
  const icon = park === 'katmai' ? <span className="katmai-fish" aria-hidden>🐟</span> : <span className="yellowstone-bison" aria-hidden>🦬</span>
  const renderLink = (t) => (
    <a key={t} href={parkHref(park, t)} className={link(t === tab)} aria-current={t === tab ? 'page' : undefined}>
      {icon}
      {t}
    </a>
  )

  return (
    <>
      <div className="desktop-nav">
        <nav className="flex flex-wrap gap-1" aria-label="Primary park sections">
          {['cameras', 'analytics'].map(renderLink)}
        </nav>
      </div>
      <div className="mobile-nav">
        <nav className="flex flex-wrap gap-1" aria-label="Park sections">
          {TABS.map(renderLink)}
        </nav>
      </div>
    </>
  )
}
