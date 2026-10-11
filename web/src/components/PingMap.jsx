import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useMemo, useRef, useState } from 'react'
import { FLAT_STYLE, pingPopup } from '../lib/mapStyle'
import { distanceKm, speciesFor, toGeoJSON } from '../lib/pings'
import { timeAgo } from '../lib/time'
import { useMode } from '../lib/useMode'
import { usePingFlow } from '../lib/usePingFlow'
import { usePings } from '../lib/usePings'
import PingSheet from './PingSheet'

maplibregl.setWorkerUrl(workerUrl)

// Small flat satellite map of one park: its pings (last 24 h), camera markers where a camera has coordinates,
// and a Drop ping button (GPS in Live mode, tap-the-map in Demo mode).
export default function PingMap({ park, cameras, className = '' }) {
  const holder = useRef()
  const mapRef = useRef()
  const [ready, setReady] = useState(false)
  const { mode } = useMode()
  const { pings, post } = usePings(mode)
  const flow = usePingFlow({ mode, post, park: park.slug, parkName: park.name })
  const flowRef = useRef(flow)
  flowRef.current = flow

  const inPark = useMemo(
    () => pings.filter((p) => distanceKm(p.lat, p.lng, park.lat, park.lng) <= park.radiusKm),
    [pings, park],
  )

  useEffect(() => {
    const map = new maplibregl.Map({ container: holder.current, style: FLAT_STYLE, center: [park.lng, park.lat], zoom: 8, attributionControl: { compact: true } })
    mapRef.current = map
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.on('click', (e) => flowRef.current.place(e.lngLat.lat, e.lngLat.lng))
    // The card is flex-sized and loads lazily: re-measure whenever its box changes.
    const resize = new ResizeObserver(() => map.resize())
    resize.observe(holder.current)
    map.on('load', () => {
      map.addSource('pings', { type: 'geojson', data: toGeoJSON([]) })
      map.addLayer({
        id: 'ping-point', type: 'circle', source: 'pings',
        paint: {
          'circle-color': ['case', ['get', 'sample'], '#a78bfa', '#f97316'],
          'circle-radius': 7, 'circle-stroke-width': 2, 'circle-stroke-color': '#fff',
        },
      })
      map.on('click', 'ping-point', (e) => {
        const f = e.features[0]
        new maplibregl.Popup({ offset: 10 }).setLngLat(f.geometry.coordinates).setDOMContent(pingPopup(f.properties, timeAgo)).addTo(map)
      })
      map.on('mouseenter', 'ping-point', () => (map.getCanvas().style.cursor = 'pointer'))
      map.on('mouseleave', 'ping-point', () => (map.getCanvas().style.cursor = flowRef.current.placing ? 'crosshair' : ''))
      setReady(true)
    })
    return () => {
      resize.disconnect()
      map.remove()
    }
  }, [park])

  useEffect(() => {
    if (ready) mapRef.current.getSource('pings').setData(toGeoJSON(inPark))
  }, [ready, inPark])

  useEffect(() => {
    if (ready) mapRef.current.getCanvas().style.cursor = flow.placing ? 'crosshair' : ''
  }, [ready, flow.placing])

  // Camera markers, only for cameras that have coordinates.
  useEffect(() => {
    if (!ready) return
    const markers = cameras
      .filter((c) => c.park === park.slug && Number.isFinite(c.lat) && Number.isFinite(c.lng))
      .map((c) => {
        const el = document.createElement('div')
        el.textContent = '📷'
        el.title = c.name
        el.style.cssText = 'font-size:18px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.7))'
        return new maplibregl.Marker({ element: el }).setLngLat([c.lng, c.lat]).addTo(mapRef.current)
      })
    return () => markers.forEach((m) => m.remove())
  }, [ready, cameras, park.slug])

  return (
    <section className={`park-map-card relative overflow-hidden rounded-2xl border border-stone-200 bg-black shadow-sm ${className}`} aria-label={`${park.name} pings`}>
      <div className="absolute inset-0"><div ref={holder} className="h-full w-full" /></div>
      <p className="pointer-events-none absolute left-2 top-2 rounded-md bg-black/60 px-2 py-1 text-xs text-white">📍 Pings near {park.name} · last 24 h</p>
      <div className="absolute inset-x-0 bottom-2 flex flex-col items-center gap-1.5 px-2">
        {flow.msg && <p className="rounded-lg bg-black/75 px-3 py-1 text-center text-xs text-white">{flow.msg}</p>}
        <button type="button" onClick={flow.start} className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:bg-emerald-500">
          {flow.placing ? 'Tap the map…' : '📍 Drop ping'}
        </button>
      </div>
      {flow.here && <PingSheet fixed demo={flow.here.demo} species={speciesFor(flow.here.lat, flow.here.lng)} onSubmit={flow.submit} onCancel={flow.cancel} />}
    </section>
  )
}
