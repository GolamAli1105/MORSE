import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { supabase } from "../lib/supabase";
import type { User as SupabaseUser, AuthError } from "@supabase/supabase-js";

interface AuthContextValue {
  user: SupabaseUser | null;
  loading: boolean;
  signIn: (email: string, password: string, rememberMe?: boolean) => Promise<{ error: AuthError | null }>;
  signUp: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signInWithGoogle: () => Promise<{ error: AuthError | null }>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    (async () => {
      // Get current session
      const { data, error } = await supabase.auth.getSession();
      if (!error && mounted) {
        setUser(data?.session?.user ?? null);
      }
      setLoading(false);
    })();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  // ✅ Fixed signIn with Remember Me
  const signIn = async (email: string, password: string, rememberMe: boolean = true) => {
    // Set session persistence based on rememberMe
    await supabase.auth.setSession({
      access_token: '',
      refresh_token: '',
    });
    
    const { data, error } = await supabase.auth.signInWithPassword({ 
      email, 
      password,
      options: {
        // If rememberMe is false, session will expire when browser closes
        // If true, session persists in localStorage
        persistSession: rememberMe
      }
    });
    
    if (!error && data?.user) setUser(data.user);
    return { error: error as AuthError | null };
  };

  // ✅ Fixed signUp
  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (!error && data?.user) setUser(data.user);
    return { error: error as AuthError | null };
  };

  // ✅ Fixed signInWithGoogle
  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    return { error: error as AuthError | null };
  };

  // ✅ Fixed resetPassword - using code exchange flow
  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });
    return { error: error as AuthError | null };
  };

  // ✅ signOut unchanged
  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn,
        signUp,
        signInWithGoogle,
        resetPassword,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;


