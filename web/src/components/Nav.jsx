const link = (active) =>
  `rounded-lg px-3 py-1.5 text-sm font-medium ${
    active ? 'bg-emerald-100 text-emerald-800' : 'text-stone-600 hover:bg-stone-100'
  }`

export default function Nav({ route }) {
  return (
    <nav className="flex gap-1" aria-label="Main">
      <a href="#/" className={link(route.name === 'feed')} aria-current={route.name === 'feed' ? 'page' : undefined}>
        Feed
      </a>
      <a
        href="#/cameras"
        className={link(route.name === 'cameras' || route.name === 'camera')}
        aria-current={route.name === 'cameras' || route.name === 'camera' ? 'page' : undefined}
      >
        Cameras
      </a>
    </nav>
  )
}
