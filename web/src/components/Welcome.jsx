import { useEffect, useRef } from 'react'

// Full-screen blur over the live globe. The only way in is the button.
export default function Welcome({ closing, onBegin }) {
  const btn = useRef(null)
  useEffect(() => btn.current?.focus(), [])
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
      className={`welcome fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 px-6 text-center text-white backdrop-blur-md bg-black/35 transition-opacity duration-[600ms] ${closing ? 'pointer-events-none opacity-0' : 'opacity-100'}`}
    >
      <h1 id="welcome-title" className="text-4xl font-bold drop-shadow sm:text-5xl">En-Vision</h1>
      <p className="max-w-sm text-base text-white/85 sm:text-lg">Wildlife sightings from cameras in the parks</p>
      <button
        ref={btn}
        onClick={onBegin}
        className="mt-2 rounded-full bg-emerald-600 px-8 py-3 text-lg font-semibold text-white shadow-lg hover:bg-emerald-500 focus:outline-none focus-visible:ring-4 focus-visible:ring-white/70"
      >
        Begin
      </button>
    </div>
  )
}
