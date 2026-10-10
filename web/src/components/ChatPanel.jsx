import { makeMockChat } from '../lib/mock'
import { useThread } from '../lib/useThread'
import ThreadPanel from './ThreadPanel'

const pretty = (park) => park.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

// One live chat room per park.
export default function ChatPanel({ park }) {
  const { messages, post, error, usingMock } = useThread('chat_messages', 'park', park, makeMockChat(park))
  return (
    <ThreadPanel
      title={`${pretty(park)} chat`}
      messages={messages}
      onPost={post}
      usingMock={usingMock}
      error={error}
      empty="No messages yet. Say hi to other visitors."
    />
  )
}
