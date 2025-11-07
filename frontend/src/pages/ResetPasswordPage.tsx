import React, { useState, useEffect } from 'react';
import { Lock, Eye, EyeOff } from 'lucide-react';
import { InputField } from '../auth/InputField';
import { supabase } from '../lib/supabase';

export const ResetPasswordPage = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [sessionReady, setSessionReady] = useState(false);
  const [initializing, setInitializing] = useState(true);

  // Check for existing session (Supabase handles the token exchange automatically)
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log('Full URL:', window.location.href);
        console.log('Hash:', window.location.hash);
        console.log('Search:', window.location.search);
        
        // Check for error in URL
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const hashError = hashParams.get('error');
        const hashErrorDescription = hashParams.get('error_description');
        
        if (hashError) {
          console.error('Error in URL:', hashError, hashErrorDescription);
          const errorMsg = hashErrorDescription?.replace(/\+/g, ' ') || hashError;
          setError(`Reset link error: ${errorMsg}. Please request a new password reset.`);
          setInitializing(false);
          return;
        }

        // Wait a moment for Supabase to process the URL
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check if we have a session (Supabase client should have handled the token)
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        console.log('Session check:', { 
          hasSession: !!session, 
          sessionError,
          user: session?.user?.email 
        });

        if (sessionError) {
          console.error('Session error:', sessionError);
          setError(`Failed to verify session: ${sessionError.message}. Please request a new password reset.`);
          setInitializing(false);
          return;
        }

        if (!session) {
          console.error('No session found');
          setError('No active session found. The reset link may have expired or is invalid. Please request a new password reset.');
          setInitializing(false);
          return;
        }

        // Session exists - ready to reset password
        console.log('Session ready for password reset');
        setSessionReady(true);
        setInitializing(false);
      } catch (err) {
        console.error('Error checking session:', err);
        setError(`An error occurred: ${err instanceof Error ? err.message : 'Unknown error'}. Please request a new password reset.`);
        setInitializing(false);
      }
    };

    checkSession();
  }, []);

  const togglePasswordVisibility = () => setShowPassword(!showPassword);

  // Function to reset password using Supabase v2
  const resetPasswordWithToken = async (password: string) => {
    // The session should already be established from the recovery link
    // Just update the password directly
    const { error } = await supabase.auth.updateUser({ password });
    return { error };
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!sessionReady) {
      setError('Session not ready. Please try again or request a new password reset.');
      return;
    }

    try {
      setLoading(true);
      
      // Verify we have an active session before updating
      const { data: sessionData } = await supabase.auth.getSession();
      if (!sessionData.session) {
        throw new Error('No active session. Please request a new password reset.');
      }

      const { error } = await resetPasswordWithToken(newPassword);
      if (error) throw error;
      setMessage('Password updated successfully! Redirecting to login...');
      setNewPassword('');
      setConfirmPassword('');
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Show loading state while initializing
  if (initializing) {
    return (
      <div className="w-full max-w-md mx-auto min-h-screen flex flex-col justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Verifying Reset Link...</h1>
          <p className="text-slate-400">Please wait</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto min-h-screen flex flex-col justify-center">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <Lock className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">Reset Password</h1>
        <p className="text-slate-400 text-lg">Set a new password for your account</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-300 text-sm backdrop-blur-sm">
          {error}
        </div>
      )}
      {message && (
        <div className="mb-6 p-4 bg-green-900/30 border border-green-500/30 rounded-xl text-green-300 text-sm backdrop-blur-sm">
          {message}
        </div>
      )}

      <form onSubmit={handleReset} className="space-y-6">
        <div className="relative">
          <InputField
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={loading || !sessionReady}
            className="bg-white/5 border-white/10 focus:border-purple-500 focus:ring-purple-500/20"
            icon={<Lock className="text-slate-400" size={18} />}
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3 bottom-3 text-slate-400 hover:text-slate-200"
            disabled={!sessionReady}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <div className="relative">
          <InputField
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading || !sessionReady}
            className="bg-white/5 border-white/10 focus:border-purple-500 focus:ring-purple-500/20"
            icon={<Lock className="text-slate-400" size={18} />}
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3 bottom-3 text-slate-400 hover:text-slate-200"
            disabled={!sessionReady}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <button
          type="submit"
          disabled={loading || !sessionReady}
          className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5"
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Resetting...
            </div>
          ) : (
            'Reset Password'
          )}
        </button>
      </form>
    </div>
  );
};
