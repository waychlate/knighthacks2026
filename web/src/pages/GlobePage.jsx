import { useEffect, useMemo, useRef, useState } from 'react'
import Globe from 'react-globe.gl'
import { PARKS, sightingsToday } from '../lib/parks'
import { parkHref } from '../lib/useRoute'

// Markers only show once the camera is closer than this (globe radii above the surface).
const SHOW_BELOW_ALTITUDE = 1.2
const isTouch = () => window.matchMedia('(hover: none)').matches

function Card({ park, stats, onOpen, touch }) {
  return (
    <div className="pointer-events-auto absolute bottom-6 left-1/2 w-[min(22rem,calc(100%-2rem))] -translate-x-1/2 rounded-2xl bg-white/95 p-4 shadow-lg">
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

export default function GlobePage({ sightings, cameras }) {
  const ref = useRef()
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight })
  const [zoomed, setZoomed] = useState(false)
  const [picked, setPicked] = useState(null)
  const touch = isTouch()

  useEffect(() => {
    const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight })
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    ref.current?.pointOfView({ lat: 45, lng: -115, altitude: 2.2 })
    ref.current.controls().minDistance = 115 // stop zooming just above the surface
  }, [])

  const open = (p) => {
    window.location.hash = parkHref(p.slug).slice(1)
  }

  const stats = useMemo(
    () =>
      Object.fromEntries(
        PARKS.map((p) => [p.slug, { cameras: cameras.filter((c) => c.park === p.slug).length, today: sightingsToday(p.slug, sightings, cameras) }]),
      ),
    [sightings, cameras],
  )

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <Globe
        ref={ref}
        width={size.w}
        height={size.h}
        globeImageUrl="/globe/earth.jpg"
        bumpImageUrl="/globe/bump.png"
        backgroundColor="#000000"
        atmosphereColor="#6ee7b7"
        onZoom={({ altitude }) => setZoomed(altitude < SHOW_BELOW_ALTITUDE)}
        pointsData={zoomed ? PARKS : []}
        pointLat="lat"
        pointLng="lng"
        pointAltitude={0.02}
        pointRadius={0.25}
        pointColor={(p) => (p.active ? '#34d399' : '#fbbf24')}
        pointLabel={() => ''}
        onPointHover={(p) => !touch && setPicked(p ?? null)}
        onPointClick={(p) => (touch ? setPicked(p) : open(p))}
        onGlobeClick={() => touch && setPicked(null)}
      />

      <div className="pointer-events-none absolute inset-x-0 top-0 p-4 text-center text-white">
        <h1 className="text-2xl font-bold drop-shadow">🦌 Animal Logger</h1>
        <p className={`text-sm text-white/80 transition-opacity ${zoomed ? 'opacity-0' : 'opacity-100'}`}>
          Spin the globe and zoom in to find parks
        </p>
      </div>

      {picked && <Card park={picked} stats={stats[picked.slug]} onOpen={() => open(picked)} touch={touch} />}
    </div>
  )
}
