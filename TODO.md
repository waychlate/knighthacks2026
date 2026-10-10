# En-Vision PWA TODO

Frontend-only checklist for turning Animal Logger into a polished, installable Progressive Web App. The backend, Supabase data layer, worker, and existing API contracts remain unchanged.

## PWA foundation

- [x] Install and configure `vite-plugin-pwa`.
- [x] Create `web/public/manifest.webmanifest`.
- [x] Add the manifest link and mobile metadata to `web/index.html`.
- [x] Add app icons: 192px, 512px, maskable, Apple touch icon, and favicon.
- [x] Set the app name to `En-Vision`.
- [x] Set the short name to `En-Vision`.
- [x] Set the theme color to the forest-green brand color.
- [x] Set the background color to the warm off-white brand color.
- [x] Configure standalone display mode.
- [x] Add the service worker.
- [x] Register the service worker in the React app.
- [x] Cache the application shell and static assets.
- [x] Add an offline fallback screen or banner.
- [x] Avoid caching sensitive or user-specific API responses.
- [x] Add a service-worker update notice when a new version is available.

## Mobile app shell

- [x] Make the header compact on phone-sized screens.
- [x] Add a mobile-friendly app logo and title.
- [x] Add fixed bottom navigation for Feed, Cameras, Analytics, and the floating Chat entry point.
- [x] Keep the desktop navigation at larger breakpoints.
- [x] Add bottom safe-area spacing for phones with home indicators.
- [x] Add enough page padding so fixed navigation cannot cover content.
- [x] Make all navigation controls large enough for touch.
- [x] Prevent horizontal page scrolling.
- [x] Keep Demo/Live mode switching easy to access on mobile.

## Feed and sightings

- [x] Make sighting cards stack vertically on narrow screens.
- [x] Keep animal images large enough to recognize.
- [x] Prevent timestamps and confidence values from being squeezed.
- [x] Make camera links easy to tap.
- [x] Keep comment controls touch-friendly.
- [x] Add loading skeletons instead of plain loading text.
- [x] Improve the empty state with a useful message and visual treatment.
- [x] Make the prediction card compact on mobile.
- [x] Add colored species or confidence indicators if they improve scanning.

## Filters

- [x] Make species and camera filters full width on phones.
- [x] Add a clear `Filters` label.
- [x] Make the active-filter state obvious.
- [x] Keep the clear-filters button easy to find.
- [x] Consider a collapsible filter drawer for smaller screens.

## Camera pages

- [x] Keep the camera feed full width on mobile.
- [x] Stack detected animals below the camera on small screens.
- [x] Keep the species count bar readable and wrapping correctly.
- [x] Make camera title and location compact.
- [x] Make video controls usable on touch screens.
- [x] Keep the live/demo status visible.
- [x] Ensure the floating chat does not cover video controls or important content.
- [x] Add bottom spacing for mobile navigation.

## Floating chat

- [x] Keep the chat bubble above mobile navigation.
- [x] Add safe-area bottom spacing.
- [x] Make the compact preview fit narrow screens.
- [x] Make expanded chat nearly full width on phones.
- [x] Ensure the keyboard does not hide the message input.
- [x] Keep minimize, expand, and close controls accessible.
- [x] Confirm chat does not cover important controls.
- [x] Test chat in portrait and landscape orientations.

## Analytics

- [x] Reduce chart heights on mobile.
- [x] Keep chart labels readable on narrow screens.
- [x] Allow charts to scroll horizontally when needed.
- [x] Avoid overlapping axis labels.
- [x] Stack chart cards vertically.
- [x] Add accessible text summaries for every chart.

## Responsive visual polish

- [x] Use a consistent spacing scale.
- [x] Use consistent rounded cards and borders.
- [x] Add pressed states for touch controls.
- [x] Add subtle loading and page transitions.
- [x] Use a consistent icon style.
- [x] Add a wildlife, mountain, or camera mark to the app identity.
- [x] Maintain strong contrast in bright outdoor conditions.
- [x] Respect reduced-motion preferences.
- [ ] Consider a dark forest mode later.

## Offline behavior

- [x] Cache the app shell.
- [x] Cache icons and static demo assets.
- [x] Show an offline status message when the connection is lost.
- [x] Allow previously loaded screens to remain usable offline.
- [x] Explain when fresh sightings cannot be loaded.
- [x] Clearly label stale data and never present it as live. (Offline banner and the Live · offline mode label identify cached/offline data.)
- [x] Add a retry action when the connection returns.

## Accessibility

- [x] Give every button an accessible label.
- [x] Give every image useful alt text.
- [x] Verify keyboard navigation.
- [x] Keep focus indicators visible.
- [x] Verify color contrast.
- [x] Use touch targets of at least approximately 44px.
- [x] Verify screen-reader navigation labels.
- [x] Add text summaries for charts.
- [x] Give chat states clear accessible labels.

## Testing

- [x] Run `npm run lint`.
- [x] Run `npm run test`.
- [x] Run `npm run build`.
- [x] Run `npm run preview`.
- [ ] Test Chrome desktop.
- [ ] Test Chrome Android.
- [ ] Test Safari iPhone.
- [ ] Test Safari iPad.
- [ ] Test Edge desktop.
- [x] Test a narrow phone viewport.
- [x] Test a large phone viewport.
- [x] Test tablet portrait and landscape.
- [x] Verify there is no horizontal scrolling.
- [ ] Verify the app manifest in browser DevTools.
- [x] Verify the service worker is registered.
- [x] Verify the offline shell loads.
- [ ] Verify install behavior on supported browsers.
- [ ] Verify app icons and splash-screen colors.
- [x] Verify browser back navigation and refresh behavior.

## Deployment

- [ ] Confirm Vercel serves the manifest.
- [ ] Confirm Vercel serves the service worker.
- [ ] Push PWA changes to GitHub `main`.
- [ ] Confirm Vercel starts a new deployment.
- [ ] Test the deployed HTTPS site.
- [ ] Install the deployed app on a phone.
- [ ] Test the installed version.
- [ ] Confirm later deployments update the installed app.

## Recommended implementation order

1. Add the manifest, icons, and service worker.
2. Build the mobile app shell and bottom navigation.
3. Make the feed and camera pages responsive.
4. Adjust the floating chat for mobile safe areas.
5. Improve loading, empty, and offline states.
6. Complete accessibility and device testing.
7. Deploy and test installation from the HTTPS Vercel site.
