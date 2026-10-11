import { makeMockChat } from '../lib/mock'
import { useThread } from '../lib/useThread'
import ThreadPanel from './ThreadPanel'

const pretty = (park) => park.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

// One live chat room per park. An inline panel on every screen size (on phones it is the Chat tab).
export default function ChatPanel({ park }) {
  const { messages, post, error, usingMock } = useThread('chat_messages', 'park', park, makeMockChat(park))
  const title = `${pretty(park)} chat`
  const latest = messages[messages.length - 1]

  return (
    <section className="desktop-chat-panel rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label={title}>
      <div className={`flex items-center justify-between gap-3 bg-emerald-700 px-4 py-3 text-white ${park === 'katmai' ? 'katmai-canopy' : ''}`}>
        <div>
          <h3 className="font-semibold">💬 {title}</h3>
          {usingMock && <span className="text-xs text-emerald-100">sample chat</span>}
        </div>
        {latest && <span className="text-xs text-emerald-100">Live room</span>}
      </div>
      <div className="flex min-h-0 flex-1 flex-col p-4">
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
