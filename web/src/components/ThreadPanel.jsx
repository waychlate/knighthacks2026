import { useEffect, useRef, useState } from 'react'
import { MAX_BODY, validateMessage } from '../lib/moderation'
import { getDisplayName } from '../lib/settings'

const input =
  'w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'

// Shared UI for the park chat and for comments on a sighting. Anonymous: a display name and a message.
export default function ThreadPanel({ title, messages, onPost, usingMock, empty, compact = false, error }) {
  const [name] = useState(getDisplayName) // changed in Settings
  const [body, setBody] = useState('')
  const [problem, setProblem] = useState(null)
  const [sending, setSending] = useState(false)
  const lastSent = useRef(0)
  const list = useRef(null)

  useEffect(() => {
    if (list.current) list.current.scrollTop = list.current.scrollHeight
  }, [messages.length])

  async function submit(e) {
    e.preventDefault()
    const v = validateMessage(name, body, { lastSentAt: lastSent.current })
    if (!v.ok) return setProblem(v.error)
    setSending(true)
    const err = await onPost(v.name, v.body)
    setSending(false)
    if (err) return setProblem(err)
    lastSent.current = Date.now()
    setBody('')
    setProblem(null)
  }

  const idPrefix = title.replace(/\W+/g, '-').toLowerCase()
  return (
    <section aria-label={title} className={compact ? 'mt-3 border-t border-stone-100 pt-3' : 'rounded-xl border border-stone-200 bg-white p-4 shadow-sm'}>
      {!compact && (
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="font-semibold text-stone-900">{title}</h3>
          {usingMock && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">sample chat</span>}
        </div>
      )}
      {error && <p className="mb-2 rounded bg-red-50 px-2 py-1 text-sm text-red-700">Could not load messages: {error}</p>}
      <ul ref={list} aria-live="polite" className={`${compact ? 'max-h-40' : 'max-h-64'} space-y-2 overflow-y-auto`}>
        {messages.length === 0 && <li className="text-sm text-stone-500">{empty}</li>}
        {messages.map((m) => (
          <li key={m.id} className="text-sm">
            <span className="font-medium text-stone-800">{m.display_name}</span>{' '}
            <span className="text-xs text-stone-400">{new Date(m.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
            <p className="break-words text-stone-700">{m.body}</p>
          </li>
        ))}
      </ul>
      <form onSubmit={submit} className="mt-3 space-y-2">
        <p className="text-xs text-stone-500">Posting as <span className="font-medium text-stone-700">{name}</span> · <a href="#/settings" className="text-emerald-700 underline">Change</a></p>
        <div className="flex gap-2">
          <label className="sr-only" htmlFor={`${idPrefix}-body`}>Message</label>
          <input id={`${idPrefix}-body`} className={`${input} min-w-0 flex-1`} placeholder="Say something about the animals…" value={body} onChange={(e) => setBody(e.target.value)} />
          <button
            type="submit"
            disabled={sending || !body.trim() || body.length > MAX_BODY}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-1 disabled:opacity-50"
          >
            Send
          </button>
        </div>
        <p className="flex justify-between text-xs">
          <span role={problem ? 'alert' : undefined} className={problem ? 'text-red-600' : 'text-stone-400'}>
            {problem ?? 'Anonymous. Keep it friendly.'}
          </span>
          <span className={body.length > MAX_BODY ? 'text-red-600' : 'text-stone-400'}>
            {body.length}/{MAX_BODY}
          </span>
        </p>
      </form>
    </section>
  )
}
