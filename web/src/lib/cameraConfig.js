// How each camera is shown. The NPS Yellowstone "Electric Peak" cam has a live still image (liveImage);
// the Katmai cams are explore.org live video (stream); every other camera is demo-only. Cameras are matched by name so this works for both mock and
// Supabase rows. Image credit: National Park Service.

export const NPS_ELECTRIC_PEAK = 'https://www.nps.gov/webcams-yell/mammoth_electric.jpg'

// Katmai: explore.org live video, shown in Live mode only. `youtubeId` = the explore.org YouTube live,
// embedded click-to-load. Stream IDs change between seasons: if an embed says unavailable, update them
// (find the current live on explore.org or the @explorebears YouTube channel).
const EXPLORE_CREDIT = 'explore.org with the National Park Service'
const explore = (youtubeId) => ({ stream: { youtubeId, page: `https://www.youtube.com/watch?v=${youtubeId}` }, credit: EXPLORE_CREDIT })

const CONFIG = {
  'Brooks Falls Bearcam': explore('J7ZrIDvqlic'),
  'Brooks Falls Low Cam': explore('EwTH5yY7Mks'),
  'River Watch Cam': explore('wkVLYfU-Kew'),
  'Electric Peak Cam': { liveImage: NPS_ELECTRIC_PEAK, demoVideo: '/demo/electric-peak.mp4', credit: 'National Park Service' },
  'Lamar Valley Demo Cam': { demoVideo: '/demo/lamar-valley.mp4', credit: 'National Park Service (recorded clip)' },
  'Hayden Valley Demo Cam': { demoVideo: '/demo/hayden-valley.mp4', credit: 'National Park Service (recorded clip)' },
}

export function cameraMedia(camera) {
  return CONFIG[camera?.name] ?? {}
}

export const hasLiveFeed = (camera) => {
  const m = cameraMedia(camera)
  return Boolean(m.liveImage || m.stream)
}

// Brooks Falls bears are there mid-June to late October; outside that the explore.org cams replay old
// highlights. Same rule as the worker (worker/animal_worker/main.py in_bear_season).
export function bearSeasonNote(now = new Date()) {
  const md = (now.getMonth() + 1) * 100 + now.getDate()
  return md >= 615 && md <= 1031 ? null : 'Outside bear season (mid-June to late October) this stream shows highlights from past years.'
}
