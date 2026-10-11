import { useState } from 'react'
import { PARKS } from '../lib/parks'

export default function ParkSearch({ onPick }) {
  const [q, setQ] = useState('')
  const term = q.trim().toLowerCase()
  const results = term ? PARKS.filter((p) => p.name.toLowerCase().includes(term)) : []
  const pick = (park) => {
    setQ('')
    onPick(park)
  }
  return (
    <div className="relative w-64">
      {term && (
        <ul className="absolute bottom-full mb-2 w-full overflow-hidden rounded-xl bg-white text-sm shadow-lg" role="listbox">
          {results.length === 0 && <li className="px-3 py-2 text-stone-500">No parks found</li>}
          {results.map((p) => (
            <li key={p.slug}>
              <button type="button" onClick={() => pick(p)} className="block w-full px-3 py-2 text-left text-stone-900 hover:bg-stone-100">
                {p.name}
                {!p.active && <span className="block text-xs text-stone-500">Cameras coming soon</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && results[0] && pick(results[0])}
        placeholder="🔍 Search parks"
        aria-label="Search parks"
        className="w-full rounded-full bg-white/95 px-4 py-2 text-sm text-stone-900 shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
      />
    </div>
  )
}
