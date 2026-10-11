import { useEffect, useState } from 'react'
import { bearSeasonNote, cameraMedia } from '../lib/cameraConfig'
import { LIVE_REFRESH_MS, liveImageUrl } from '../lib/live'
import { useMode } from '../lib/useMode'

function Bubble({ live, unavailable }) {
  const style = unavailable ? 'bg-stone-700 text-stone-100' : live ? 'bg-emerald-600 text-white' : 'bg-amber-500 text-white'
  return (
    <span role="status" className={`absolute left-3 top-3 z-10 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold shadow ${style}`}>
      {live && !unavailable && <span className="h-2 w-2 animate-pulse rounded-full bg-white" aria-hidden />}
      {unavailable ? 'Live (unavailable)' : live ? 'Live' : 'Demo clip'}
    </span>
  )
}

// Live video from explore.org. Nothing is requested from YouTube until the visitor presses play.
function StreamPanel({ camera, media }) {
  const [playing, setPlaying] = useState(false)
  const { youtubeId, page } = media.stream
  const note = bearSeasonNote()
  return (
    <figure>
      <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-stone-900">
        <Bubble live />
        {playing && youtubeId ? (
          <iframe
            className="h-full w-full"
            src={`https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&mute=1&rel=0`}
            title={`Live video: ${camera.name}`}
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
            allowFullScreen
            referrerPolicy="strict-origin-when-cross-origin"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-gradient-to-br from-sky-900 to-stone-900 px-4 text-center text-white">
            <span className="text-4xl" aria-hidden>🐻</span>
            <p className="text-sm text-sky-100">Live video from explore.org</p>
            {youtubeId && (
              <button onClick={() => setPlaying(true)} className="rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-stone-900 hover:bg-sky-100">
                ▶ Watch live
              </button>
            )}
            <a href={page} target="_blank" rel="noopener noreferrer" className="text-sm text-sky-200 underline">
              {youtubeId ? 'Open on YouTube ↗' : 'Watch on explore.org ↗'}
            </a>
          </div>
        )}
      </div>
      <figcaption className="mt-1 text-xs text-stone-500">
        Live video, not recorded by us. AI detections are sampled about once a minute while our detector is running. Credit: {media.credit}.
        {note && <span className="mt-1 block text-amber-700">{note}</span>}
      </figcaption>
    </figure>
  )
}

// The camera view. Demo mode loops a recorded clip; Live mode shows the latest still, refreshed every
// minute. Live never falls back to the demo clip: if the image fails we say so.
export default function CameraPanel({ camera }) {
  const { mode } = useMode()
  const media = cameraMedia(camera)
  const live = mode === 'live'
  const [stamp, setStamp] = useState(() => Date.now())
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!live || !media.liveImage) return
    setFailed(false)
    setStamp(Date.now())
    const timer = setInterval(() => setStamp(Date.now()), LIVE_REFRESH_MS)
    return () => clearInterval(timer)
  }, [live, media.liveImage])

  const frame = 'relative aspect-video w-full overflow-hidden rounded-xl'

  if (live && media.stream) return <StreamPanel camera={camera} media={media} />

  if (live && !media.liveImage) {
    return (
      <div className={`${frame} flex items-center justify-center bg-stone-200`}>
        <p className="px-4 text-center text-sm text-stone-600">No live feed for this camera. Switch to Demo to see a recorded clip.</p>
      </div>
    )
  }
  if (!live && !media.demoVideo) {
    return (
      <div className={`${frame} flex items-center justify-center bg-stone-200`}>
        <p className="px-4 text-center text-sm text-stone-600">
          {media.stream ? 'This camera is live video only. Switch to Live to watch.' : 'No demo clip for this camera.'}
        </p>
      </div>
    )
  }

  return (
    <figure>
      <div className={`${frame} bg-stone-900`}>
        <Bubble live={live} unavailable={live && failed} />
        {live ? (
          <>
            <img
              key={stamp}
              src={liveImageUrl(media.liveImage, stamp)}
              alt={`Latest image from ${camera.name}`}
              className="h-full w-full object-cover"
              onLoad={() => setFailed(false)}
              onError={() => setFailed(true)}
            />
            {failed && (
              <div className="absolute inset-0 flex items-center justify-center bg-stone-900/80">
                <p className="px-4 text-center text-sm text-stone-100">Live feed unavailable. We will keep trying every minute.</p>
              </div>
            )}
          </>
        ) : (
          <video
            key={media.demoVideo}
            src={media.demoVideo}
            className="h-full w-full object-cover"
            autoPlay
            loop
            muted
            playsInline
            controls
            aria-label={`Recorded demo clip for ${camera.name}`}
          />
        )}
      </div>
      <figcaption className="mt-1 text-xs text-stone-500">
        {live ? 'Image refreshes about every minute.' : 'A recorded clip, not a live feed.'} Credit: {media.credit}.
      </figcaption>
    </figure>
  )
}
