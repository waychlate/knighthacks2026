const link = (active) =>
  `rounded-lg px-3 py-1.5 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
    active ? 'bg-emerald-100 text-emerald-800' : 'text-stone-600 hover:bg-stone-100'
  }`

const ITEMS = [
  ['feed', '#/', 'Feed', ['feed']],
  ['cameras', '#/cameras', 'Cameras', ['cameras', 'camera']],
  ['analytics', '#/analytics', 'Analytics', ['analytics']],
]

export default function Nav({ route }) {
  return (
    <nav className="flex gap-1" aria-label="Main">
      {ITEMS.map(([key, href, label, names]) => {
        const active = names.includes(route.name)
        return (
          <a key={key} href={href} className={link(active)} aria-current={active ? 'page' : undefined}>
            {label}
          </a>
        )
      })}
    </nav>
  )
}
