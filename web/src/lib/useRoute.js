import { useEffect, useState } from 'react'

// Tiny hash router: #/ (globe), #/park/:slug[/tab], #/camera/:id. No dependency needed.
// Old routes #/cameras and #/analytics redirect into Yellowstone.
export const TABS = ['sightings', 'cameras', 'predictions', 'chat', 'analytics']

function parse(hash) {
  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean)
  if (parts[0] === 'park' && parts[1]) {
    const tab = TABS.includes(parts[2]) ? parts[2] : 'sightings'
    return { name: 'park', park: decodeURIComponent(parts[1]), tab }
  }
  if (parts[0] === 'cameras' || parts[0] === 'analytics') return { name: 'park', park: 'yellowstone', tab: parts[0] }
  if (parts[0] === 'camera' && parts[1]) return { name: 'camera', id: decodeURIComponent(parts[1]) }
  return { name: 'globe' }
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
export const parkHref = (slug, tab = 'sightings') => `#/park/${encodeURIComponent(slug)}/${tab}`
