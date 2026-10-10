import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'prompt',
      includeAssets: ['favicon.svg', 'apple-touch-icon.svg'],
      manifest: {
        name: 'En-Vision',
        short_name: 'En-Vision',
        description: 'A calm, accessible wildlife camera and sighting log.',
        theme_color: '#166534',
        background_color: '#fafaf9',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          { src: '/icons/icon-192.svg', sizes: '192x192', type: 'image/svg+xml' },
          { src: '/icons/icon-512.svg', sizes: '512x512', type: 'image/svg+xml' },
          { src: '/icons/icon-maskable.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webmanifest,mp4}'],
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        navigateFallback: 'index.html',
        runtimeCaching: [],
      },
    }),
  ],
  // .env lives at the repo root so the worker and web app share one file
  envDir: '..',
  // Also expose the public names Vercel's Supabase integration sets. Keep this prefix narrow:
  // SUPABASE_SERVICE_ROLE_KEY must never match, or it would be bundled into the browser code.
  envPrefix: ['VITE_', 'NEXT_PUBLIC_SUPABASE_'],
})
