import { lazy, Suspense } from 'react'
import ChatPanel from '../components/ChatPanel'
import Nav, { navTab } from '../components/Nav'
import PredictionCard from '../components/PredictionCard'
import { getPark } from '../lib/parks'
import { useIsPhone } from '../lib/useIsPhone'
import { usePredictions } from '../lib/usePredictions'
import AnalyticsPage from './AnalyticsPage'
import CamerasPage from './CamerasPage'
import FeedPage from './FeedPage'

const PingMap = lazy(() => import('../components/PingMap')) // MapLibre is heavy: load it only on park pages

function ParkMap({ park, cameras, className }) {
  return <Suspense fallback={<div className={`park-map-card rounded-2xl bg-stone-200 ${className}`} />}><PingMap park={park} cameras={cameras} className={className} /></Suspense>
}

function Predictions({ park }) {
  return <PredictionCard park={park} {...usePredictions()} />
}

export default function ParkPage({ slug, tab, sightings, cameras, loading, mode }) {
  const park = getPark(slug)
  const parkCameras = cameras.filter((c) => c.park === slug)
  const ids = new Set(parkCameras.map((c) => c.id))
  const parkSightings = sightings.filter((s) => ids.has(s.camera.id))
  const phone = useIsPhone()
  const view = navTab(tab) // Sightings and Predictions are sections of the Cameras page
  const themeClass = slug === 'katmai' ? 'katmai-theme' : slug === 'yellowstone' ? 'yellowstone-theme' : 'forest-theme'

  return (
    <div className={`${themeClass} ${slug === 'katmai' ? 'katmai-environment' : ''} ${slug === 'yellowstone' ? 'yellowstone-environment' : ''}`}>
      <div className="park-layout">
        <section className="park-main-column">
          {slug === 'katmai' && <div className="river-background" aria-hidden="true" />}
          {slug === 'yellowstone' && <div className="yellowstone-trail-background" aria-hidden="true" />}
          <div className="mb-4">
            <h2 className="text-xl font-bold text-stone-900">{park?.name ?? slug}</h2>
            {park?.region && <p className="text-sm text-stone-500">{park.region}</p>}
            {slug === 'yellowstone' && <div className="yellowstone-trail" aria-hidden><span>🦬</span><span>━━━</span><span>♨</span></div>}
          </div>

          {!park?.active ? (
            <>
              <Nav park={slug} tab="chat" limited />
              <p className="rounded-lg bg-stone-100 px-3 py-4 text-stone-600">
                📷 Cameras coming soon for {park?.name ?? slug}. You can still chat with other visitors and drop a ping on the map.
              </p>
              {phone && park && (
                <div className="mt-4 space-y-4">
                  <ParkMap park={park} cameras={parkCameras} className="park-map-phone" />
                  <ChatPanel park={slug} />
                </div>
              )}
            </>
          ) : (
            <>
              <div className="mb-5"><Nav park={slug} tab={tab} /></div>
              {view === 'cameras' && (
                <div className="desktop-camera-dashboard">
                  {phone && park && <ParkMap park={park} cameras={parkCameras} className="park-map-phone" />}
                  <section className="desktop-dashboard-section" aria-labelledby={`${slug}-camera-views`}>
                    <h3 id={`${slug}-camera-views`} className="desktop-section-title">Camera views</h3>
                    <CamerasPage park={slug} sightings={parkSightings} cameras={parkCameras} />
                  </section>
                  <section className="desktop-dashboard-section" aria-labelledby={`${slug}-predictions`}>
                    <h3 id={`${slug}-predictions`} className="desktop-section-title">Predictions</h3>
                    <Predictions park={slug} />
                  </section>
                  <section className="desktop-dashboard-section" aria-labelledby={`${slug}-recent-sightings`}>
                    <h3 id={`${slug}-recent-sightings`} className="desktop-section-title">Recent sightings</h3>
                    <FeedPage sightings={parkSightings} cameras={parkCameras} loading={loading} mode={mode} />
                  </section>
                </div>
              )}
              {view === 'chat' && phone && <div className="mobile-chat-route"><div className="katmai-chat-zone"><ChatPanel park={slug} /></div></div>}
              {view === 'analytics' && <AnalyticsPage park={slug} sightings={parkSightings} loading={loading} mode={mode} />}
            </>
          )}
        </section>
        <aside className="desktop-chat-sidebar" aria-label={`${park?.name ?? slug} chat`}>
          {!phone && <ChatPanel park={slug} />}
          {!phone && park && <ParkMap park={park} cameras={parkCameras} />}
        </aside>
      </div>
    </div>
  )
}
