import { useState } from 'react'
import { MAX_NAME } from '../lib/moderation'
import { getDev, getDisplayName, setDev, setDisplayName } from '../lib/settings'

const input =
  'w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'

export default function SettingsPage() {
  const [name, setName] = useState(getDisplayName)
  const [saved, setSaved] = useState(false)
  const [dev, setDevState] = useState(getDev)

  function saveName(e) {
    e.preventDefault()
    const clean = setDisplayName(name)
    if (clean) setName(clean)
    setSaved(Boolean(clean))
  }

  return (
    <div className="max-w-xl space-y-4">
      <h2 className="text-xl font-bold text-stone-900">Settings</h2>

      <form onSubmit={saveName} className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
        <label htmlFor="settings-name" className="font-semibold text-stone-900">Chat display name</label>
        <p className="mb-2 text-sm text-stone-500">Shown on your chat messages and comments. Anonymous: no account, saved only in this browser.</p>
        <div className="flex gap-2">
          <input id="settings-name" className={input} value={name} maxLength={MAX_NAME} onChange={(e) => { setName(e.target.value); setSaved(false) }} />
          <button type="submit" disabled={!name.trim()} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50">Save</button>
        </div>
        {saved && <p role="status" className="mt-2 text-sm text-emerald-700">Saved.</p>}
      </form>

      <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
        <label className="flex items-start gap-3">
          <input type="checkbox" className="mt-1 h-4 w-4" checked={dev} onChange={(e) => { setDevState(e.target.checked); setDev(e.target.checked) }} />
          <span>
            <span className="font-semibold text-stone-900">Dev mode</span>
            <span className="block text-sm text-stone-500">Show detection details (annotated frames, box and confidence) once they are available. Off by default.</span>
          </span>
        </label>
      </div>

      <p className="text-sm text-stone-500">The Demo / Live switch stays in the header.</p>
    </div>
  )
}
