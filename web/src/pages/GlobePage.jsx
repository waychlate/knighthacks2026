import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useMemo, useRef, useState } from 'react'
import PingSheet from '../components/PingSheet'
import { useMode } from '../lib/useMode'
import { PARKS, sightingsToday } from '../lib/parks'
import { cooldownLeftMs, markPinged, toGeoJSON } from '../lib/pings'
import { timeAgo } from '../lib/time'
import { usePings } from '../lib/usePings'
import { parkHref } from '../lib/useRoute'

// Vite must bundle MapLibre's worker (it imports a shared chunk), so hand it the built URL.
maplibregl.setWorkerUrl(workerUrl)

// Park markers show once the map is zoomed in past this level.
const SHOW_PARKS_ZOOM = 4
const isTouch = () => window.matchMedia('(hover: none)').matches

// Imagery © Esri (no key; credited on screen). Terrain from the free AWS Terrarium tiles.
// Labels use glyphs hosted by MapLibre's demo server: a runtime dependency, like the tiles.
const STYLE = {
  version: 8,
  projection: { type: 'globe' },
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sources: {
    imagery: {
      type: 'raster',
      tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
      tileSize: 256,
      maxzoom: 18,
      attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
    },
    terrain: {
      type: 'raster-dem',
      tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 14,
      encoding: 'terrarium',
    },
  },
  layers: [
    { id: 'bg', type: 'background', paint: { 'background-color': '#000000' } },
    { id: 'imagery', type: 'raster', source: 'imagery' },
  ],
  terrain: { source: 'terrain', exaggeration: 1.5 },
}

function Card({ park, stats, onOpen, touch }) {
  return (
    <div className="pointer-events-auto absolute bottom-24 left-1/2 z-10 w-[min(22rem,calc(100%-2rem))] -translate-x-1/2 rounded-2xl bg-white/95 p-4 shadow-lg">
      <p className="font-semibold text-stone-900">🌲 {park.name}</p>
      <p className="text-sm text-stone-500">{park.region}</p>
      {park.active ? (
        <p className="mt-2 text-sm text-stone-700">
          {stats.cameras} camera{stats.cameras === 1 ? '' : 's'} · {stats.today} sighting{stats.today === 1 ? '' : 's'} today
        </p>
      ) : (
        <p className="mt-2 text-sm text-stone-500">No cameras yet.</p>
      )}
      {touch ? (
        <button onClick={onOpen} className="mt-3 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white">
          Open park
        </button>
      ) : (
        <p className="mt-2 text-xs text-stone-400">Click the marker to open</p>
      )}
    </div>
  )
}

// Popup content built with DOM nodes and textContent: ping notes are user input, never inject them as HTML.
function pingPopup(p) {
  const el = document.createElement('div')
  el.style.cssText = 'font:14px system-ui;color:#1c1917;max-width:220px'
  const line = (text, css) => {
    const d = document.createElement('div')
    d.textContent = text
    d.style.cssText = css ?? ''
    el.appendChild(d)
  }
  line(p.species || 'Something spotted', 'font-weight:600')
  if (p.note) line(p.note)
  line(`${timeAgo(p.created_at)} · ${p.sample === true || p.sample === 'true' ? 'sample ping' : 'user-reported'}`, 'color:#78716c;font-size:12px;margin-top:2px')
  return el
}

export default function GlobePage({ sightings, cameras }) {
  const holder = useRef()
  const mapRef = useRef()
  const [ready, setReady] = useState(false)
  const [zoomed, setZoomed] = useState(false)
  const [picked, setPicked] = useState(null)
  const [here, setHere] = useState(null) // position waiting for the ping sheet
  const [msg, setMsg] = useState(null)
  const touch = isTouch()
  const { mode } = useMode()
  const { pings, post } = usePings(mode)

  const stats = useMemo(
    () =>
      Object.fromEntries(
        PARKS.map((p) => [p.slug, { cameras: cameras.filter((c) => c.park === p.slug).length, today: sightingsToday(p.slug, sightings, cameras) }]),
      ),
    [sightings, cameras],
  )

  useEffect(() => {
    const map = new maplibregl.Map({ container: holder.current, style: STYLE, center: [-115, 45], zoom: 2.2, maxPitch: 70, attributionControl: { compact: true } })
    mapRef.current = map
    map.on('error', (e) => console.error('maplibre:', e.error?.message ?? e))
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')

    const markers = PARKS.map((park) => {
      const el = document.createElement('button')
      el.setAttribute('aria-label', park.name)
      el.style.cssText = `display:none;width:22px;height:22px;border-radius:50%;border:3px solid #fff;cursor:pointer;background:${park.active ? '#34d399' : '#fbbf24'}`
      const open = () => {
        window.location.hash = parkHref(park.slug).slice(1)
      }
      if (!touch) {
        el.addEventListener('mouseenter', () => setPicked(park))
        el.addEventListener('mouseleave', () => setPicked(null))
      }
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        if (touch) setPicked(park)
        else open()
      })
      new maplibregl.Marker({ element: el }).setLngLat([park.lng, park.lat]).addTo(map)
      return el
    })

    const onZoom = () => {
      const z = map.getZoom() >= SHOW_PARKS_ZOOM
      setZoomed(z)
      markers.forEach((el) => (el.style.display = z ? 'block' : 'none'))
    }
    map.on('zoom', onZoom)
    map.on('click', () => touch && setPicked(null))

    map.on('load', () => {
      map.addSource('pings', { type: 'geojson', data: toGeoJSON([]), cluster: true, clusterRadius: 40, clusterMaxZoom: 10 })
      map.addLayer({
        id: 'ping-clusters', type: 'circle', source: 'pings', filter: ['has', 'point_count'],
        paint: { 'circle-color': '#6366f1', 'circle-radius': ['step', ['get', 'point_count'], 14, 10, 18, 50, 24], 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' },
      })
      map.addLayer({
        id: 'ping-count', type: 'symbol', source: 'pings', filter: ['has', 'point_count'],
        layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': ['Open Sans Semibold'], 'text-size': 12, 'text-allow-overlap': true },
        paint: { 'text-color': '#fff' },
      })
      map.addLayer({
        id: 'ping-point', type: 'circle', source: 'pings', filter: ['!', ['has', 'point_count']],
        paint: { 'circle-color': ['case', ['get', 'near'], '#34d399', '#9ca3af'], 'circle-radius': 7, 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' },
      })
      map.on('click', 'ping-clusters', async (e) => {
        const f = e.features[0]
        const zoom = await map.getSource('pings').getClusterExpansionZoom(f.properties.cluster_id)
        map.easeTo({ center: f.geometry.coordinates, zoom })
      })
      map.on('click', 'ping-point', (e) => {
        const f = e.features[0]
        new maplibregl.Popup({ offset: 10 }).setLngLat(f.geometry.coordinates).setDOMContent(pingPopup(f.properties)).addTo(map)
      })
      for (const id of ['ping-clusters', 'ping-point']) {
        map.on('mouseenter', id, () => (map.getCanvas().style.cursor = 'pointer'))
        map.on('mouseleave', id, () => (map.getCanvas().style.cursor = ''))
      }
      setReady(true)
    })
    return () => map.remove()
  }, [touch])

  useEffect(() => {
    if (ready) mapRef.current.getSource('pings').setData(toGeoJSON(pings))
  }, [ready, pings])

  function startPing() {
    setMsg(null)
    const left = cooldownLeftMs(window.localStorage)
    if (left > 0) return setMsg(`One ping per 5 minutes. Try again in ${Math.ceil(left / 60000)} min.`)
    if (!navigator.geolocation) return setMsg('Your browser cannot share its location.')
    navigator.geolocation.getCurrentPosition(
      (pos) => setHere({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => setMsg(err.code === 1 ? 'Location permission was denied, so no ping was sent.' : 'Could not get your location.'),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  async function submitPing(extra) {
    const err = await post({ ...here, ...extra })
    if (err) return err
    markPinged(window.localStorage)
    mapRef.current.flyTo({ center: [here.lng, here.lat], zoom: 9 })
    setHere(null)
    setMsg('Ping dropped. Thanks!')
    return null
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <div className="absolute inset-0"><div ref={holder} className="h-full w-full" /></div>

      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 p-4 text-center text-white">
        <h1 className="text-2xl font-bold drop-shadow">🦌 Animal Logger</h1>
        <p className={`text-sm text-white/80 transition-opacity ${zoomed ? 'opacity-0' : 'opacity-100'}`}>
          Spin the globe and zoom in to find parks
        </p>
      </div>

      {picked && <Card park={picked} stats={stats[picked.slug]} onOpen={() => (window.location.hash = parkHref(picked.slug).slice(1))} touch={touch} />}

      <div className="absolute bottom-6 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-2">
        {msg && <p className="rounded-lg bg-black/70 px-3 py-1.5 text-sm text-white">{msg}</p>}
        <button onClick={startPing} className="rounded-full bg-emerald-600 px-5 py-3 font-medium text-white shadow-lg hover:bg-emerald-500">
          📍 Drop ping
        </button>
      </div>

      {here && <PingSheet onSubmit={submitPing} onCancel={() => setHere(null)} />}
    </div>
  )
}
