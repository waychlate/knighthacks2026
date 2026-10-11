import { useEffect, useRef, useState } from 'react'
import { MAX_NAME } from '../lib/moderation'
import { getDev, getDisplayName, setDev, setDisplayName } from '../lib/settings'

const input =
  'w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'

// Floating window over the current page: closes on Escape, the backdrop, or the close button.
export default function SettingsPage({ onClose }) {
  const [name, setName] = useState(getDisplayName)
  const [saved, setSaved] = useState(false)
  const [dev, setDevState] = useState(getDev)
  const closeBtn = useRef(null)
  useEffect(() => {
    closeBtn.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  function saveName(e) {
    e.preventDefault()
    const clean = setDisplayName(name)
    if (clean) setName(clean)
    setSaved(Boolean(clean))
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="max-h-full w-full max-w-md space-y-4 overflow-y-auto rounded-2xl bg-stone-50 p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
      <div className="flex items-center justify-between">
        <h2 id="settings-title" className="text-xl font-bold text-stone-900">Settings</h2>
        <button ref={closeBtn} type="button" onClick={onClose} aria-label="Close settings" className="rounded-lg px-2 py-1 text-xl leading-none text-stone-600 hover:bg-stone-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500">×</button>
      </div>

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
    </div>
  )
}
