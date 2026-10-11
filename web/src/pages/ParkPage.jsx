import ChatPanel from '../components/ChatPanel'
import Nav from '../components/Nav'
import PredictionCard from '../components/PredictionCard'
import { getPark } from '../lib/parks'
import { usePredictions } from '../lib/usePredictions'
import AnalyticsPage from './AnalyticsPage'
import CamerasPage from './CamerasPage'
import FeedPage from './FeedPage'

function Predictions() {
  return <PredictionCard {...usePredictions()} />
}

const KATMAI_CAMERA_PREVIEWS = [
  ['Brooks Falls Bear Cam', 'Bear watch · coming soon'],
  ['Salmon River Cam', 'River view · coming soon'],
  ['Katmai Bear Watch', 'Alaska wildlife · coming soon'],
]

function KatmaiCameraPreviews() {
  return (
    <>
      <p className="mb-3 rounded-lg bg-stone-100 px-3 py-4 text-stone-600">Camera links and live stats will be connected later.</p>
      <ul className="grid gap-3 sm:grid-cols-2">
        {KATMAI_CAMERA_PREVIEWS.map(([name, detail]) => (
          <li key={name}>
            <div aria-disabled="true" className="camera-card katmai-camera-card opacity-90">
              <p className="font-semibold text-stone-900">🐻 {name}</p>
              <p className="text-sm text-stone-500">{detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </>
  )
}

export default function ParkPage({ slug, tab, sightings, cameras, loading, mode }) {
  const park = getPark(slug)
  const parkCameras = cameras.filter((c) => c.park === slug)
  const ids = new Set(parkCameras.map((c) => c.id))
  const parkSightings = sightings.filter((s) => ids.has(s.camera.id))
  const themeClass = slug === 'katmai' ? 'katmai-theme' : slug === 'yellowstone' ? 'yellowstone-theme' : 'forest-theme'

  return (
    <div className={`${themeClass} ${slug === 'katmai' ? 'katmai-environment' : ''} ${slug === 'yellowstone' ? 'yellowstone-environment' : ''}`}>
      <div className="mb-4">
        <a href="#/" className="back-button mb-3"><span className="back-arrow" aria-hidden>←</span> Globe</a>
        <h2 className="text-xl font-bold text-stone-900">{park?.name ?? slug}</h2>
        {park?.region && <p className="text-sm text-stone-500">{park.region}</p>}
        {slug === 'katmai' && <div className="katmai-waterline" aria-hidden><span>🐟</span><span>〰</span><span>🐟</span></div>}
        {slug === 'yellowstone' && <div className="yellowstone-trail" aria-hidden><span>🦬</span><span>━━━</span><span>♨</span></div>}
      </div>

      {!park?.active ? (
        slug === 'katmai' && tab === 'cameras' ? <KatmaiCameraPreviews /> : <p className="rounded-lg bg-stone-100 px-3 py-4 text-stone-600">No cameras here yet. Check back later.</p>
      ) : (
        <>
          <div className="mb-5"><Nav park={slug} tab={tab} /></div>
          {tab === 'sightings' && <FeedPage sightings={parkSightings} cameras={parkCameras} loading={loading} mode={mode} />}
          {tab === 'cameras' && <CamerasPage park={slug} sightings={parkSightings} cameras={parkCameras} />}
          {tab === 'predictions' && <Predictions />}
          {tab === 'chat' && <div className="katmai-chat-zone"><ChatPanel park={slug} /></div>}
          {tab === 'analytics' && <AnalyticsPage sightings={parkSightings} loading={loading} mode={mode} />}
        </>
      )}
    </div>
  )
}
