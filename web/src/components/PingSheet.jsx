import { useState } from 'react'
import { NOTE_MAX } from '../lib/pings'

// Confirm step for a ping: optional species and note, plus the privacy notice. `species` is the list for
// the park the user is in, or null outside every park (then a free-text box).
export default function PingSheet({ species: options, onSubmit, onCancel, fixed = false, demo = false }) {
  const [species, setSpecies] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    const err = await onSubmit({ species_name: species, note: note.trim() })
    if (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <div className={`ping-sheet ${fixed ? 'fixed z-[80]' : 'absolute z-20'} inset-0 flex items-end justify-center bg-black/50 p-4 sm:items-center`}>
      <form onSubmit={submit} className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold text-stone-900">📍 Drop a ping</h2>
        <p className="mt-1 text-xs text-stone-500">
          {demo ? 'Demo ping: it stays in this browser only and is never shared.' : 'Your approximate location (about 500 m) will be shared publicly for 24 hours. This is a user report, not a camera detection.'}
        </p>
        <label className="mt-4 block text-sm text-stone-700">
          What did you see? (optional)
          {options ? (
            <select value={species} onChange={(e) => setSpecies(e.target.value)} className="mt-1 w-full rounded-lg border border-stone-300 px-2 py-2">
              <option value="">Not sure / something else</option>
              {options.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          ) : (
            <input
              value={species}
              maxLength={60}
              onChange={(e) => setSpecies(e.target.value)}
              placeholder="e.g. great blue heron"
              className="mt-1 w-full rounded-lg border border-stone-300 px-2 py-2"
            />
          )}
        </label>
        <label className="mt-3 block text-sm text-stone-700">
          Note (optional)
          <textarea
            value={note}
            maxLength={NOTE_MAX}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-stone-300 px-2 py-2"
          />
          <span className="text-xs text-stone-400">{note.length}/{NOTE_MAX}</span>
        </label>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100">
            Cancel
          </button>
          <button disabled={busy} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {busy ? 'Posting…' : 'Drop ping'}
          </button>
        </div>
      </form>
    </div>
  )
}
