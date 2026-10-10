// How each camera is shown. Only the NPS Yellowstone "Electric Peak" cam has a real live image;
// every other camera is demo-only. Cameras are matched by name so this works for both mock and
// Supabase rows. Image credit: National Park Service.

export const NPS_ELECTRIC_PEAK = 'https://www.nps.gov/webcams-yell/mammoth_electric.jpg'

const CONFIG = {
  'Electric Peak Cam': { liveImage: NPS_ELECTRIC_PEAK, demoVideo: '/demo/electric-peak.mp4', credit: 'National Park Service' },
  'Lamar Valley Demo Cam': { demoVideo: '/demo/lamar-valley.mp4', credit: 'National Park Service (recorded clip)' },
  'Hayden Valley Demo Cam': { demoVideo: '/demo/hayden-valley.mp4', credit: 'National Park Service (recorded clip)' },
}

export function cameraMedia(camera) {
  return CONFIG[camera?.name] ?? {}
}

export const hasLiveFeed = (camera) => Boolean(cameraMedia(camera).liveImage)
