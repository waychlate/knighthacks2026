import { useEffect, useState } from 'react'

const STORAGE_KEY = 'envision-theme'

function readTheme() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      window.localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // The theme still applies for this session when storage is unavailable.
    }
  }, [theme])

  const dark = theme === 'dark'
  return (
    <button
      type="button"
      className="theme-toggle rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100"
      aria-pressed={dark}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark forest theme'}
      onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
    >
      <span aria-hidden>{dark ? '☀' : '☾'}</span> {dark ? 'Light' : 'Dark'}
    </button>
  )
}
