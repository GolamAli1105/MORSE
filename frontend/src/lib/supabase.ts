import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

const mockClient = {
  auth: {
    signInWithOAuth: async () => ({ error: { message: 'Supabase not configured. Add env vars.' } }),
    signInWithPassword: async () => ({ error: { message: 'Supabase not configured. Add env vars.' } }),
    signUp: async () => ({ error: { message: 'Supabase not configured. Add env vars.' } }),
    resetPasswordForEmail: async () => ({ error: { message: 'Supabase not configured. Add env vars.' } }),
    updateUser: async () => ({ error: { message: 'Supabase not configured. Add env vars.' } }),
    setSession: async () => ({ data: { session: null }, error: { message: 'Supabase not configured. Add env vars.' } }),
    getSession: async () => ({ data: { session: null }, error: null }),
    onAuthStateChange: () => ({
      data: {
        subscription: { unsubscribe: () => {} },
      },
    }),
    signOut: async () => ({ error: null }),
  },
} as unknown as SupabaseClient; // 👈 force TS to treat it like a real client

export const supabase: SupabaseClient = (() => {
  if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
      '⚠️ Supabase configuration missing. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to .env.\n' +
        'Using mock client - auth operations will fail gracefully.'
    );
    return mockClient;
  }

  try {
    return createClient(supabaseUrl, supabaseAnonKey, {
      auth: { 
        autoRefreshToken: true, 
        persistSession: true, 
        storage: window.localStorage,
        flowType: 'pkce', // Use PKCE flow for better security and reliability
        detectSessionInUrl: true, // Automatically detect and handle auth redirects
      },
    });
  } catch (err) {
    console.error('Failed to create Supabase client:', err);
    return mockClient;
  }
})();
