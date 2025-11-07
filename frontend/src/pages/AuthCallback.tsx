import { useEffect } from 'react';
import { supabase } from '../lib/supabase';

export function AuthCallback() {
  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Try to parse session from the URL (handles OAuth and magic link flows)
        // This will store the session in the client (localStorage) if successful.
  // supabase client typings in the mock may not include getSessionFromUrl, so cast to any
  const { data, error } = await (supabase.auth as any).getSessionFromUrl();

        if (error) {
          console.error('Error parsing session from URL:', error);
        } else if (!data?.session) {
          // As a fallback, check if a session is already present
          const { data: sessionData } = await supabase.auth.getSession();
          if (!sessionData?.session) {
            console.warn('No session found after auth callback');
          }
        }
      } catch (err) {
        console.error('Error handling auth callback:', err);
      } finally {
        // Clean URL and redirect to app root
        try {
          // Remove auth params from URL to avoid leaking tokens
          const cleanUrl = `${window.location.origin}/`;
          window.history.replaceState({}, document.title, cleanUrl);
        } catch (e) {
          // fallback
          window.location.href = '/';
        }
      }
    };

    handleAuthCallback();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">Completing login...</h2>
        <p className="text-slate-600">Please wait while we finish setting up your session.</p>
      </div>
    </div>
  );
}