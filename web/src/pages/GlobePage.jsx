import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useMemo, useRef, useState } from 'react'
import PingSheet from '../components/PingSheet'
import StarField from '../components/StarField'
import Welcome from '../components/Welcome'
import { IMAGERY_SOURCE, pingPopup } from '../lib/mapStyle'
import { useMode } from '../lib/useMode'
import { usePingFlow } from '../lib/usePingFlow'
import { latestSighting, PARKS, sightingsToday } from '../lib/parks'
import { distanceKm, speciesFor, toGeoJSON } from '../lib/pings'
import { timeAgo } from '../lib/time'
import { usePings } from '../lib/usePings'
import { parkHref } from '../lib/useRoute'
import { markWelcomeSeen, welcomeSeen } from '../lib/welcome'

// Vite must bundle MapLibre's worker (it imports a shared chunk), so hand it the built URL.
maplibregl.setWorkerUrl(workerUrl)

// Park markers show once the map is zoomed in past this level (2.6 is a few scroll notches from the start).
const SHOW_PARKS_ZOOM = 2.6
// Zoomed in this far with the map centred inside a park, its overview panel opens at the bottom.
const OVERVIEW_ZOOM = 7
// Set when a park is entered; the next globe mount starts at the park and zooms back out to `view`.
let returnTo = null
const snapshot = (map) => {
  const c = map.getCenter()
  return { center: [c.lng, c.lat], zoom: map.getZoom(), pitch: map.getPitch(), bearing: map.getBearing() }
}
const isTouch = () => window.matchMedia('(hover: none)').matches

// Imagery © Esri (no key; credited on screen). Terrain from the free AWS Terrarium tiles.
// Labels use glyphs hosted by MapLibre's demo server: a runtime dependency, like the tiles.
const STYLE = {
  version: 8,
  projection: { type: 'globe' },
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sources: {
    imagery: IMAGERY_SOURCE,
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

function Card({ park, stats, latest, onOpen, onBack, showButton }) {
  return (
    <div className="globe-card pointer-events-auto absolute bottom-24 left-1/2 z-10 w-[min(22rem,calc(100%-2rem))] -translate-x-1/2 rounded-2xl bg-white/95 p-4 shadow-lg">
      <p className="font-semibold text-stone-900">🌲 {park.name}</p>
      <p className="text-sm text-stone-500">{park.region}</p>
      {park.active ? (
        <p className="mt-2 text-sm text-stone-700">
          {stats.cameras} camera{stats.cameras === 1 ? '' : 's'} · {stats.today} sighting{stats.today === 1 ? '' : 's'} today
        </p>
      ) : (
        <p className="mt-2 text-sm text-stone-500">No cameras yet.</p>
      )}
      {park.active && (
        <p className="mt-1 text-sm text-stone-500">
          {latest ? `Latest: ${latest.species.common_name} · ${timeAgo(latest.seen_at)}` : 'No sightings yet in this mode.'}
        </p>
      )}
      {showButton ? (
        <div className="mt-3 flex gap-2">
          <button onClick={onOpen} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white">
            Open park
          </button>
          {onBack && (
            <button onClick={onBack} className="rounded-lg bg-stone-200 px-3 py-1.5 text-sm font-medium text-stone-800">
              Back
            </button>
          )}
        </div>
      ) : (
        <p className="mt-2 text-xs text-stone-400">Click the marker to zoom in</p>
      )}
    </div>
  )
}

// Popup content built with DOM nodes and textContent: ping notes are user input, never inject them as HTML.
export default function GlobePage({ sightings, cameras }) {
  const holder = useRef()
  const mapRef = useRef()
  const [ready, setReady] = useState(false)
  const [zoomed, setZoomed] = useState(false)
  const [picked, setPicked] = useState(null) // park under the pointer / tapped
  const [focus, setFocus] = useState(null) // park the map is zoomed in over
  const touch = isTouch()
  const { mode } = useMode()
  const { pings, post, error: pingsError, usingMock } = usePings(mode)
  const flow = usePingFlow({ mode, post, onDropped: (at) => mapRef.current?.flyTo({ center: [at.lng, at.lat], zoom: 9 }) })
  const flowRef = useRef(flow)
  flowRef.current = flow
  const { here, msg } = flow

  const shown = picked ?? focus

  // Entering a park: fly in slowly, fade to the app background, then switch route.
  const [leaving, setLeaving] = useState(0) // 0 = no, 1 = flying, 2 = fading
  const enterRef = useRef()
  // Back from a park page: start covered by the app background, fade out while the map zooms out.
  const [arriving, setArriving] = useState(() => (returnTo ? 1 : 0))
  useEffect(() => {
    if (arriving === 1) setTimeout(() => setArriving(2), 50)
  }, [arriving])
  const [previewing, setPreviewing] = useState(null) // park the visitor zoomed into but has not opened
  const view = useRef(null) // camera before the preview, to zoom back out to
  const previewRef = useRef()
  const backRef = useRef()
  const preview = (park) => {
    if (leaving || previewing?.slug === park.slug) return
    const map = mapRef.current
    if (!previewing) {
      view.current = snapshot(map)
    }
    setPreviewing(park)
    setPicked(null)
    map.flyTo({ center: [park.lng, park.lat], zoom: 11, pitch: 50, duration: 2000 })
  }
  const back = () => {
    if (!previewing || leaving) return
    setPreviewing(null)
    mapRef.current.flyTo({ ...view.current, duration: 2000 })
    view.current = null
  }
  previewRef.current = preview
  backRef.current = back
  const enter = (park) => {
    if (leaving) return
    const go = () => {
      returnTo = { park, view: view.current ?? snapshot(mapRef.current) }
      setLeaving(2)
      setTimeout(() => (window.location.hash = parkHref(park.slug).slice(1)), 500)
    }
    if (previewing?.slug === park.slug || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return go()
    setLeaving(1)
    setPicked(null)
    let done = false
    const finish = () => !done && ((done = true), go())
    mapRef.current.flyTo({ center: [park.lng, park.lat], zoom: 11, pitch: 50, duration: 2500 })
    mapRef.current.once('moveend', finish)
    setTimeout(finish, 4000) // tiles or an interruption must not strand the visitor
  }
  enterRef.current = enter

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && backRef.current()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // 'open' -> 'closing' (600 ms fade) -> 'done'
  const [welcome, setWelcome] = useState(() => (welcomeSeen() ? 'done' : 'open'))
  const begin = () => {
    markWelcomeSeen()
    setWelcome('closing')
    setTimeout(() => setWelcome('done'), 600)
  }
  const stage = useRef(null)
  useEffect(() => {
    if (welcome === 'open') stage.current.setAttribute('inert', '')
    else stage.current.removeAttribute('inert')
  }, [welcome])
  // Slow spin behind the blur (skipped for reduced motion).
  useEffect(() => {
    if (welcome !== 'open' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let raf
    const spin = () => {
      const map = mapRef.current
      if (map && !map.isMoving()) {
        const c = map.getCenter()
        map.setCenter([((c.lng + 180.04) % 360) - 180, c.lat])
      }
      raf = requestAnimationFrame(spin)
    }
    raf = requestAnimationFrame(spin)
    return () => cancelAnimationFrame(raf)
  }, [welcome])

  const stats = useMemo(
    () =>
      Object.fromEntries(
        PARKS.map((p) => [p.slug, { cameras: cameras.filter((c) => c.park === p.slug).length, today: sightingsToday(p.slug, sightings, cameras) }]),
      ),
    [sightings, cameras],
  )

  useEffect(() => {
    const back = returnTo // coming back from a park page
    const start = back ? { center: [back.park.lng, back.park.lat], zoom: 11, pitch: 50 } : { center: [-115, 45], zoom: 2.2 }
    const map = new maplibregl.Map({ container: holder.current, style: STYLE, ...start, maxPitch: 70, attributionControl: { compact: true } })
    mapRef.current = map
    map.on('error', (e) => console.error('maplibre:', e.error?.message ?? e))
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')

    // Park markers are map pins (user pings are circles). Same colour for every park; parks without
    // cameras are dimmed. The wrapper is positioned by MapLibre, so the shape lives on a child.
    const markers = PARKS.map((park) => {
      const el = document.createElement('div')
      const accent = park.slug === 'katmai' ? '#0369a1' : '#047857'
      el.style.cssText = 'display:none;cursor:pointer;position:relative;width:148px;height:76px;transition:opacity .2s ease'
      el.setAttribute('role', 'button')
      el.setAttribute('aria-label', park.name)
      const halo = document.createElement('div')
      halo.style.cssText = `position:absolute;left:50%;bottom:10px;width:52px;height:52px;transform:translateX(-50%);border-radius:50%;background:${accent};opacity:.18;box-shadow:0 0 0 7px rgba(255,255,255,.22),0 0 22px ${accent}`
      const pin = document.createElement('div')
      pin.style.cssText = `position:absolute;left:50%;bottom:18px;width:40px;height:40px;background:${accent};border:3px solid #fff;border-radius:50% 50% 50% 0;transform:translateX(-50%) rotate(-45deg);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 9px rgba(0,0,0,.55);opacity:${park.active ? 1 : 0.82}`
      const icon = document.createElement('span')
      icon.textContent = '🌲'
      icon.style.cssText = 'transform:rotate(45deg);font-size:18px;line-height:1'
      const label = document.createElement('span')
      label.textContent = park.name.replace(' National Park', '')
      label.style.cssText = `position:absolute;left:50%;bottom:-1px;transform:translateX(-50%);white-space:nowrap;border:1px solid rgba(255,255,255,.9);border-radius:999px;padding:3px 8px;background:rgba(8,47,73,.9);color:#fff;font:600 11px/1.1 system-ui,sans-serif;letter-spacing:.01em;box-shadow:0 2px 8px rgba(0,0,0,.35)`
      pin.appendChild(icon)
      el.appendChild(halo)
      el.appendChild(pin)
      el.appendChild(label)
      if (!touch) {
        el.addEventListener('mouseenter', () => setPicked(park))
        el.addEventListener('mouseleave', () => setPicked(null))
      }
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        previewRef.current(park)
      })
      new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([park.lng, park.lat]).addTo(map)
      return el
    })

    const onZoom = () => {
      const z = map.getZoom() >= SHOW_PARKS_ZOOM
      setZoomed(z)
      markers.forEach((el) => (el.style.display = z ? 'block' : 'none'))
      const c = map.getCenter()
      const inside = map.getZoom() >= OVERVIEW_ZOOM ? PARKS.find((p) => distanceKm(c.lat, c.lng, p.lat, p.lng) <= p.radiusKm) : null
      setFocus((prev) => (prev?.slug === inside?.slug ? prev : (inside ?? null)))
    }
    map.on('zoom', onZoom)
    map.on('moveend', onZoom)
    map.on('click', (e) => {
      if (flowRef.current.place(e.lngLat.lat, e.lngLat.lng)) return // Demo mode: this tap placed a demo ping
      if (touch) setPicked(null)
      backRef.current()
    })

    map.on('load', () => {
      if (back) {
        returnTo = null
        map.flyTo({ ...back.view, duration: 2500 })
      }
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
        paint: { 'circle-color': ['case', ['get', 'near'], '#f97316', '#9ca3af'], 'circle-radius': 7, 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' },
      })
      map.on('click', 'ping-clusters', async (e) => {
        const f = e.features[0]
        const zoom = await map.getSource('pings').getClusterExpansionZoom(f.properties.cluster_id)
        map.easeTo({ center: f.geometry.coordinates, zoom })
      })
      map.on('click', 'ping-point', (e) => {
        const f = e.features[0]
        new maplibregl.Popup({ offset: 10 }).setLngLat(f.geometry.coordinates).setDOMContent(pingPopup(f.properties, timeAgo)).addTo(map)
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

  useEffect(() => {
    if (ready) mapRef.current.getCanvas().style.cursor = flow.placing ? 'crosshair' : ''
  }, [ready, flow.placing])

  return (
    <>
    {welcome !== 'done' && <Welcome closing={welcome === 'closing'} onBegin={begin} />}
    <div ref={stage} className="relative h-screen w-screen overflow-hidden bg-black">
      {leaving > 0 && <div className={`leave-fade absolute inset-0 z-40 transition-opacity duration-500 ${leaving === 2 ? 'opacity-100' : 'opacity-0'}`} />}
      {arriving > 0 && <div className={`leave-fade pointer-events-none absolute inset-0 z-40 transition-opacity duration-[800ms] ${arriving === 1 ? 'opacity-100' : 'opacity-0'}`} />}
      <StarField />
      <div className={`space-bear-orbit ${zoomed ? 'space-bear-orbit-hidden' : ''}`} aria-hidden="true">
        <div className="space-bear-drift">
          <div className="space-bear-facing">
            <div className="space-bear-float">
              <img src="/space-bear.png" alt="" />
            </div>
          </div>
        </div>
      </div>
      <div className="globe-map-layer absolute inset-0"><div ref={holder} className="h-full w-full" /></div>

      <div className="globe-brand pointer-events-none absolute inset-x-0 top-0 z-10 p-4 text-center text-white">
        <h1 className="text-2xl font-bold drop-shadow">En-Vision</h1>
        <p className={`text-sm text-white/80 transition-opacity ${zoomed ? 'opacity-0' : 'opacity-100'}`}>
          Spin the globe and zoom in to find parks
        </p>
      </div>

      {(usingMock || pingsError) && (
        <p className="globe-notice absolute left-3 z-10 max-w-xs rounded-lg bg-amber-100 px-3 py-2 text-xs text-amber-900">
          {usingMock
            ? 'Supabase keys are missing, so pings are not saved: they vanish when you reload.'
            : `Could not load pings: ${pingsError}. Has supabase/pings.sql been run?`}
        </p>
      )}

      {shown && (
        <Card
          park={shown}
          stats={stats[shown.slug]}
          latest={latestSighting(shown.slug, sightings, cameras)}
          onOpen={() => enter(shown)}
          onBack={previewing?.slug === shown.slug ? back : null}
          showButton={touch || shown === focus}
        />
      )}

      <div className="globe-actions absolute bottom-6 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-2">
        {msg && <p className="rounded-lg bg-black/70 px-3 py-1.5 text-sm text-white">{msg}</p>}
        <button onClick={flow.start} className="rounded-full bg-emerald-600 px-5 py-3 font-medium text-white shadow-lg hover:bg-emerald-500">
          📍 Drop ping
        </button>
      </div>

      {here && <PingSheet demo={here.demo} species={speciesFor(here.lat, here.lng)} onSubmit={flow.submit} onCancel={flow.cancel} />}
    </div>
    </>
  )
}
