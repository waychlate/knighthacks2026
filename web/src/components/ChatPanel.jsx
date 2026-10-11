import { useState } from 'react'
import { makeMockChat } from '../lib/mock'
import { useThread } from '../lib/useThread'
import ThreadPanel from './ThreadPanel'

const pretty = (park) => park.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

// One live chat room per park.
export default function ChatPanel({ park, desktop = false }) {
  const { messages, post, error, usingMock } = useThread('chat_messages', 'park', park, makeMockChat(park))
  const [view, setView] = useState('bubble')
  const title = `${pretty(park)} chat`
  const latest = messages[messages.length - 1]

  if (desktop) {
    return (
      <section className="desktop-chat-panel rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label={title}>
        <div className={`flex items-center justify-between gap-3 bg-emerald-700 px-4 py-3 text-white ${park === 'katmai' ? 'katmai-canopy' : ''}`}>
          <div>
            <h3 className="font-semibold">💬 {title}</h3>
            {usingMock && <span className="text-xs text-emerald-100">sample chat</span>}
          </div>
          {latest && <span className="text-xs text-emerald-100">Live room</span>}
        </div>
        <div className="max-h-[calc(100vh-12rem)] overflow-y-auto p-4">
          <ThreadPanel
            compact
            title={title}
            messages={messages}
            onPost={post}
            error={error}
            empty="No messages yet. Say hi to other visitors."
          />
        </div>
      </section>
    )
  }

  return (
    <div className={`chat-dock fixed right-4 z-50 ${park === 'katmai' ? 'katmai-chat' : ''}`}>
      {view === 'expanded' ? (
        <section className="w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xl shadow-stone-900/15" aria-label={title}>
          <div className={`flex items-center justify-between gap-3 bg-emerald-700 px-4 py-3 text-white ${park === 'katmai' ? 'katmai-canopy' : ''}`}>
            <div>
              <h3 className="font-semibold">{title}</h3>
              {usingMock && <span className="text-xs text-emerald-100">sample chat</span>}
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setView('mini')}
                aria-label="Minimize chat"
                className="rounded-lg px-2 py-1 text-lg leading-none hover:bg-emerald-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                −
              </button>
              <button
                type="button"
                onClick={() => setView('bubble')}
                aria-label="Hide chat"
                className="rounded-lg px-2 py-1 text-lg leading-none hover:bg-emerald-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                ×
              </button>
            </div>
          </div>
          <div className="max-h-[min(70vh,32rem)] overflow-y-auto p-4">
            <ThreadPanel
              compact
              title={title}
              messages={messages}
              onPost={post}
              error={error}
              empty="No messages yet. Say hi to other visitors."
            />
          </div>
        </section>
      ) : view === 'mini' ? (
        <section className="w-[min(20rem,calc(100vw-2rem))] rounded-2xl border border-stone-200 bg-white p-3 shadow-xl shadow-stone-900/15" aria-label={title}>
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h3 className="truncate font-semibold text-stone-900">💬 {title}</h3>
              <p className="truncate text-sm text-stone-500">
                {latest ? `${latest.display_name}: ${latest.body}` : 'No messages yet. Say hi.'}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <button
                type="button"
                onClick={() => setView('expanded')}
                aria-label="Expand chat"
                className="rounded-lg bg-emerald-700 px-3 py-1.5 text-sm font-semibold text-white hover:bg-emerald-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              >
                Open
              </button>
              <button
                type="button"
                onClick={() => setView('bubble')}
                aria-label="Hide chat"
                className="rounded-lg px-2 py-1.5 text-lg leading-none text-stone-500 hover:bg-stone-100 hover:text-stone-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              >
                ×
              </button>
            </div>
          </div>
        </section>
      ) : (
        <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setView('expanded')}
          aria-expanded="false"
          aria-label={`Open ${title}`}
          className="flex items-center gap-2 rounded-full bg-emerald-700 px-4 py-3 font-semibold text-white shadow-lg shadow-stone-900/20 transition hover:bg-emerald-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
        >
          <span aria-hidden>💬</span>
          Chat
        </button>
        <button
          type="button"
          onClick={() => setView('mini')}
          aria-label={`Show compact ${title}`}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white text-stone-600 shadow-lg shadow-stone-900/15 transition hover:bg-stone-100 hover:text-stone-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
        >
          −
        </button>
        </div>
      )}
    </div>
  )
}
