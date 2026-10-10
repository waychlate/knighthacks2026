import { useThread } from '../lib/useThread'
import ThreadPanel from './ThreadPanel'

// Mounted only when a sighting card is expanded, so closed cards cost nothing.
export default function Comments({ sightingId }) {
  const { messages, post, error } = useThread('comments', 'sighting_id', sightingId)
  return <ThreadPanel compact title={`comments-${sightingId}`} messages={messages} onPost={post} error={error} empty="No comments yet. Saw it too?" />
}
