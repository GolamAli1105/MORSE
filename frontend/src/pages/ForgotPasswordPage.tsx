import React, { useState } from 'react';
import { InputField } from '../auth/InputField';
import { useAuth } from '../contexts/AuthContext';

export const ForgotPasswordPage = () => {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    
    // Enhanced validation
    if (!email.trim()) {
      setError('Please enter your email address');
      setLoading(false);
      return;
    }
    
    if (!email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid email address (e.g., user@example.com)');
      setLoading(false);
      return;
    }
    
    // Additional email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address format');
      setLoading(false);
      return;
    }

    try {
      const { error } = await resetPassword(email);
      if (error) throw error;
      setMessage('Password reset instructions have been sent to your email!');
      setEmail(''); // Clear the email field
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">Reset Password</h1>
        <p className="text-slate-400 text-lg">Enter your email to receive reset instructions</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-300 text-sm backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        </div>
      )}

      {message && (
        <div className="mb-6 p-4 bg-green-900/30 border border-green-500/30 rounded-xl text-green-300 text-sm backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            {message}
          </div>
        </div>
      )}

      <form onSubmit={handlePasswordReset} className="space-y-6">
        <InputField
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
          disabled={loading}
          required
          className="bg-white/5 border-white/10 focus:border-orange-500 focus:ring-orange-500/20"
        />

        <button
          type="submit"
          disabled={loading || !email}
          className="w-full px-6 py-4 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-xl hover:from-orange-700 hover:to-red-700 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transform hover:-translate-y-0.5"
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Sending reset instructions...
            </div>
          ) : (
            'Send Reset Instructions'
          )}
        </button>
      </form>

      <div className="mt-8 text-center text-sm">
        <p className="text-slate-400">
          Remember your password?{' '}
          <button 
            onClick={() => window.dispatchEvent(new CustomEvent('switchToLogin'))}
            className="text-orange-400 hover:text-orange-300 font-medium transition-colors bg-transparent border-none cursor-pointer"
          >
            Back to login
          </button>
        </p>
        <p className="text-slate-500 text-xs mt-2">
          Check your spam folder if you don't see the email
        </p>
      </div>
    </div>
  );
};