import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// No keys configured -> the app falls back to mock data (see lib/useSightings.js)
export const supabase =
  url && anonKey && !url.includes('YOUR-PROJECT') ? createClient(url, anonKey) : null
