import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary'
import { ModeProvider } from './lib/useMode'
import { registerSW } from 'virtual:pwa-register'

const updateSW = registerSW({
  onNeedRefresh() {
    window.dispatchEvent(new CustomEvent('envision:pwa-update'))
  },
  onOfflineReady() {
    window.dispatchEvent(new CustomEvent('envision:pwa-ready'))
  },
})

window.envisionUpdateSW = updateSW

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <ModeProvider>
        <App />
      </ModeProvider>
    </ErrorBoundary>
  </StrictMode>,
)
