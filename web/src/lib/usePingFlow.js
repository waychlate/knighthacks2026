import { useState } from 'react'
import { cooldownLeftMs, markPinged, nearestPark, roundCoord } from './pings'

// The "Drop ping" flow shared by the globe and the park map.
// Live: use the device's GPS (one ping per 5 minutes). Demo: tap the map to place a demo ping (kept in this browser only).
// `park` (optional): after a live ping, say so if it landed outside that park.
export function usePingFlow({ mode, post, park, parkName, onDropped }) {
  const [here, setHere] = useState(null) // { lat, lng, demo } waiting for the ping sheet
  const [placing, setPlacing] = useState(false)
  const [msg, setMsg] = useState(null)

  function start() {
    setMsg(null)
    if (mode === 'demo') {
      setPlacing(true)
      return setMsg('Tap the map to place a demo ping.')
    }
    const left = cooldownLeftMs(window.localStorage)
    if (left > 0) return setMsg(`One ping per 5 minutes. Try again in ${Math.ceil(left / 60000)} min.`)
    if (!navigator.geolocation) return setMsg('Your browser cannot share its location.')
    navigator.geolocation.getCurrentPosition(
      (pos) => setHere({ lat: pos.coords.latitude, lng: pos.coords.longitude, demo: false }),
      (err) => setMsg(err.code === 1 ? 'Allow location to drop a ping (permission was denied).' : 'Could not get your location.'),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  // Called by the map on click. Returns true if the click was used to place a pin.
  function place(lat, lng) {
    if (!placing) return false
    setPlacing(false)
    setMsg(null)
    setHere({ lat: roundCoord(lat), lng: roundCoord(lng), demo: true })
    return true
  }

  async function submit(extra) {
    const { demo, ...at } = here
    const err = await post({ ...at, ...extra }, { demo })
    if (err) return err
    if (!demo) markPinged(window.localStorage)
    setHere(null)
    if (demo) setMsg('Demo ping placed. It stays in this browser only.')
    else if (park && nearestPark(at.lat, at.lng) !== park) setMsg(`Ping dropped. It is outside ${parkName ?? park}, so it shows on the globe, not this map.`)
    else setMsg('Ping dropped. Thanks!')
    onDropped?.(at)
    return null
  }

  function cancel() {
    setHere(null)
    setPlacing(false)
    setMsg(null)
  }

  return { here, placing, msg, start, place, submit, cancel }
}
