// Imagery © Esri (no key; credited on screen). Shared by the globe and the park map.
export const IMAGERY_SOURCE = {
  type: 'raster',
  tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
  tileSize: 256,
  maxzoom: 18,
  attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
}

// Flat satellite map (no globe projection, no terrain): fast enough for the small park map.
export const FLAT_STYLE = {
  version: 8,
  sources: { imagery: IMAGERY_SOURCE },
  layers: [
    { id: 'bg', type: 'background', paint: { 'background-color': '#000000' } },
    { id: 'imagery', type: 'raster', source: 'imagery' },
  ],
}

// Popup body for a ping (also used by the globe). Labels sample/demo pings so they are never mistaken for real ones.
export function pingPopup(p, timeAgo) {
  const el = document.createElement('div')
  el.style.cssText = 'font:14px system-ui;color:#1c1917;max-width:220px'
  const line = (text, css) => {
    const d = document.createElement('div')
    d.textContent = text
    d.style.cssText = css ?? ''
    el.appendChild(d)
  }
  const flag = (v) => v === true || v === 'true'
  line(p.species || 'Something spotted', 'font-weight:600')
  if (p.note) line(p.note)
  const kind = flag(p.demo) ? 'demo ping' : flag(p.sample) ? 'sample ping' : 'user-reported'
  line(`${timeAgo(p.created_at)} · ${kind}`, 'color:#78716c;font-size:12px;margin-top:2px')
  return el
}
