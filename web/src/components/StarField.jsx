import { useEffect, useRef } from 'react'

// Star points are [x, y] as fractions of the screen; lines join them by index.
const CONSTELLATIONS = [
  { // Big Dipper
    stars: [[0.1, 0.2], [0.15, 0.23], [0.2, 0.22], [0.25, 0.26], [0.26, 0.33], [0.33, 0.34], [0.32, 0.27]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 3]],
  },
  { // Orion
    stars: [[0.8, 0.12], [0.88, 0.13], [0.82, 0.2], [0.84, 0.21], [0.86, 0.22], [0.81, 0.3], [0.89, 0.29]],
    lines: [[0, 2], [1, 4], [2, 3], [3, 4], [2, 5], [4, 6], [0, 1]],
  },
  { // Cassiopeia
    stars: [[0.7, 0.82], [0.75, 0.88], [0.8, 0.83], [0.85, 0.89], [0.9, 0.84]],
    lines: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
]

// Animated canvas behind the (transparent-outside-the-globe) map: the whole sky turns slowly around
// the screen centre and each star twinkles on its own phase. Seeded, so resizes don't reshuffle.
export default function StarField() {
  const ref = useRef(null)
  useEffect(() => {
    const cv = ref.current
    const c = cv.getContext('2d')
    const still = matchMedia('(prefers-reduced-motion: reduce)').matches
    let seed = 7
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
    // Random stars live in a square big enough that rotation never exposes a bare corner.
    const field = Array.from({ length: 450 }, () => ({ x: rnd() * 2 - 1, y: rnd() * 2 - 1, r: 0.4 + rnd() * 1.1, a: 0.25 + rnd() * 0.65, ph: rnd() * 6.28, sp: 0.5 + rnd() * 1.5 }))
    let w, h, dpr, raf
    const size = () => {
      dpr = devicePixelRatio || 1
      w = cv.width = innerWidth * dpr
      h = cv.height = innerHeight * dpr
    }
    const frame = (ms) => {
      const t = still ? 0 : ms / 1000
      const half = Math.hypot(w, h) / 2
      const g = c.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, Math.max(w, h) * 0.7)
      g.addColorStop(0, '#0b1230')
      g.addColorStop(1, '#02030a')
      c.fillStyle = g
      c.fillRect(0, 0, w, h)
      c.save()
      c.translate(w / 2, h / 2)
      c.rotate(t * 0.01) // ~1 turn per 10 min
      for (const st of field) {
        const glow = still ? 1 : 0.55 + 0.45 * Math.sin(t * st.sp + st.ph)
        c.fillStyle = `rgba(255,255,255,${st.a * glow})`
        c.beginPath()
        c.arc(st.x * half, st.y * half, st.r * dpr, 0, 7)
        c.fill()
      }
      CONSTELLATIONS.forEach(({ stars, lines }, k) => {
        const pos = stars.map(([x, y]) => [(x - 0.5) * w, (y - 0.5) * h])
        c.strokeStyle = 'rgba(147,176,255,.35)'
        c.lineWidth = dpr
        for (const [a, b] of lines) {
          c.beginPath()
          c.moveTo(...pos[a])
          c.lineTo(...pos[b])
          c.stroke()
        }
        pos.forEach(([x, y], i) => {
          c.fillStyle = `rgba(255,255,255,${still ? 1 : 0.7 + 0.3 * Math.sin(t * 1.3 + k * 2 + i)})`
          c.beginPath()
          c.arc(x, y, 2 * dpr, 0, 7)
          c.fill()
        })
      })
      c.restore()
      if (!still) raf = requestAnimationFrame(frame)
    }
    const onResize = () => {
      size()
      if (still) frame(0)
    }
    size()
    raf = requestAnimationFrame(frame)
    addEventListener('resize', onResize)
    return () => {
      cancelAnimationFrame(raf)
      removeEventListener('resize', onResize)
    }
  }, [])
  return <canvas ref={ref} aria-hidden="true" className="absolute inset-0 h-full w-full" />
}
