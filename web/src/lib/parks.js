// Species seen per park (common names). Yellowstone and Katmai are from model knowledge, NOT checked against NPSpecies
// (Yellowstone mirrors worker/species.json). The greyed-out parks use the most-reported species in public iNaturalist
// observations (ml/data/inat/*.csv), lightly trimmed: what visitors report, not a complete checklist.
// The ping picker offers only the species of the park you are in.
const YELLOWSTONE_SPECIES = [
  'Elk', 'American bison', 'Pronghorn', 'Mule deer', 'Coyote', 'Gray wolf', 'Grizzly bear',
  'American black bear', 'Bighorn sheep', 'Moose', 'Bald eagle', 'Trumpeter swan', 'Sandhill crane', 'Red fox',
]
const KATMAI_SPECIES = [
  'Brown bear', 'Gray wolf', 'Moose', 'Caribou', 'Red fox', 'Wolverine', 'River otter', 'Bald eagle', 'Harbor seal', 'Arctic ground squirrel',
]
const YOSEMITE_SPECIES = [
  "Steller's jay", 'California ground squirrel', 'Mule deer', 'American black bear', 'Yellow-bellied marmot', 'Common raven',
  'Golden-mantled ground squirrel', "Douglas's squirrel", 'Acorn woodpecker', 'White-headed woodpecker', 'Dark-eyed junco', 'American robin',
]
const EVERGLADES_SPECIES = [
  'Great blue heron', 'White ibis', 'Anhinga', 'Great egret', 'Double-crested cormorant', 'Green heron', 'Purple gallinule',
  'Osprey', 'Wood stork', 'Red-shouldered hawk', 'Boat-tailed grackle', 'Northern mockingbird',
]
const GRAND_CANYON_SPECIES = [
  'Elk', 'Rock squirrel', 'Common raven', "Woodhouse's scrub-jay", 'Mule deer', 'Bighorn sheep', 'Cliff chipmunk',
  'California condor', 'Turkey vulture', 'Western bluebird', 'Mountain chickadee', 'Juniper titmouse',
]
const SMOKIES_SPECIES = [
  'American black bear', 'Elk', 'White-tailed deer', 'Wild turkey', 'Eastern gray squirrel', 'Groundhog', 'Northern cardinal',
  'American robin', 'Indigo bunting', 'Great blue heron', 'American red squirrel', 'Mallard',
]
const DENALI_SPECIES = [
  'Caribou', 'Arctic ground squirrel', 'Moose', 'Willow ptarmigan', 'Brown/grizzly bear', "Dall's sheep", 'Red fox',
  'Snowshoe hare', 'Canada jay', 'American red squirrel', 'Black-billed magpie', 'White-crowned sparrow',
]

// Parks shown on the globe. radiusKm: pings within it of the centre count as "in the park" (parks are big).
// active = it has cameras. Inactive parks show as grey markers ("cameras coming soon") but chat and pings still work.
export const PARKS = [
  { slug: 'yellowstone', name: 'Yellowstone National Park', region: 'Wyoming, USA', lat: 44.6, lng: -110.5, radiusKm: 60, active: true, species: YELLOWSTONE_SPECIES },
  { slug: 'katmai', name: 'Katmai National Park', region: 'Alaska, USA', lat: 58.5, lng: -155.0, radiusKm: 60, active: true, species: KATMAI_SPECIES },
  { slug: 'yosemite', name: 'Yosemite National Park', region: 'California, USA', lat: 37.85, lng: -119.55, radiusKm: 60, active: false, species: YOSEMITE_SPECIES },
  { slug: 'everglades', name: 'Everglades National Park', region: 'Florida, USA', lat: 25.4, lng: -80.9, radiusKm: 60, active: false, species: EVERGLADES_SPECIES },
  { slug: 'grand-canyon', name: 'Grand Canyon National Park', region: 'Arizona, USA', lat: 36.1, lng: -112.1, radiusKm: 60, active: false, species: GRAND_CANYON_SPECIES },
  { slug: 'great-smoky-mountains', name: 'Great Smoky Mountains National Park', region: 'Tennessee / North Carolina, USA', lat: 35.6, lng: -83.5, radiusKm: 60, active: false, species: SMOKIES_SPECIES },
  { slug: 'denali', name: 'Denali National Park', region: 'Alaska, USA', lat: 63.1, lng: -151.2, radiusKm: 60, active: false, species: DENALI_SPECIES },
]

export const getPark = (slug) => PARKS.find((p) => p.slug === slug)

// Sightings today (local time) at the park's cameras.
export function sightingsToday(slug, sightings, cameras) {
  const ids = new Set(cameras.filter((c) => c.park === slug).map((c) => c.id))
  const midnight = new Date().setHours(0, 0, 0, 0)
  return sightings.filter((s) => ids.has(s.camera.id) && new Date(s.seen_at).getTime() >= midnight).length
}

// Newest sighting at the park's cameras (the list is newest first), or undefined.
export function latestSighting(slug, sightings, cameras) {
  const ids = new Set(cameras.filter((c) => c.park === slug).map((c) => c.id))
  return sightings.find((s) => ids.has(s.camera.id))
}
