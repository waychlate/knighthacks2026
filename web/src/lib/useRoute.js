import { useEffect, useState } from 'react'

// Tiny hash router: #/ (feed), #/cameras, #/camera/:id, #/analytics. No dependency needed.
function parse(hash) {
  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean)
  if (parts[0] === 'cameras') return { name: 'cameras' }
  if (parts[0] === 'analytics') return { name: 'analytics' }
  if (parts[0] === 'camera' && parts[1]) return { name: 'camera', id: decodeURIComponent(parts[1]) }
  return { name: 'feed' }
}

export function useRoute() {
  const [route, setRoute] = useState(() => parse(window.location.hash))
  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export const cameraHref = (id) => `#/camera/${encodeURIComponent(id)}`
