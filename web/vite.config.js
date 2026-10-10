import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // .env lives at the repo root so the worker and web app share one file
  envDir: '..',
  // Also expose the public names Vercel's Supabase integration sets. Keep this prefix narrow:
  // SUPABASE_SERVICE_ROLE_KEY must never match, or it would be bundled into the browser code.
  envPrefix: ['VITE_', 'NEXT_PUBLIC_SUPABASE_'],
})
