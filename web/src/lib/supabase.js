import { createClient } from '@supabase/supabase-js'

// VITE_* are ours; NEXT_PUBLIC_SUPABASE_* are what Vercel's Supabase integration sets (see vite.config.js).
const env = import.meta.env
const url = env.VITE_SUPABASE_URL || env.NEXT_PUBLIC_SUPABASE_URL
const anonKey = env.VITE_SUPABASE_ANON_KEY || env.NEXT_PUBLIC_SUPABASE_ANON_KEY || env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

// No keys configured -> the app falls back to mock data (see lib/useSightings.js)
export const supabase =
  url && anonKey && !url.includes('YOUR-PROJECT') ? createClient(url, anonKey) : null
