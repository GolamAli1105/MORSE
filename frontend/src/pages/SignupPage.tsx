import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { FcGoogle } from 'react-icons/fc';
import { SocialButton } from '../auth/SocialButton';
import { InputField } from '../auth/InputField';
import { useAuth } from '../contexts/AuthContext';

export const SignupPage = () => {
  const { signUp, signInWithGoogle } = useAuth();
  const [signupMethod, setSignupMethod] = useState<'email' | 'social' | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const togglePasswordVisibility = () => setShowPassword(!showPassword);

  const handleGoogleSignup = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const { error } = await signInWithGoogle();
      if (error) throw error;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    // Validation
    if (!email.trim() || !password.trim()) {
      setError('Email and password are required');
      setLoading(false);
      return;
    }

    if (!email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const { error } = await signUp(email, password);
      if (error) throw error;
      setMessage('Account created successfully!');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
            />
          </svg>
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">Create Account</h1>
        <p className="text-slate-400 text-lg">Join us today and get started</p>
      </div>

      {/* Error and success messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-300 text-sm backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </div>
        </div>
      )}

      {message && (
        <div className="mb-6 p-4 bg-green-900/30 border border-green-500/30 rounded-xl text-green-300 text-sm backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            {message}
          </div>
        </div>
      )}

      {!signupMethod ? (
        <div className="space-y-4">
          <SocialButton
            icon={<FcGoogle size={24} />}
            text="Continue with Google"
            onClick={handleGoogleSignup}
            disabled={loading}
            className="bg-white/10 hover:bg-white/20 border border-white/20 backdrop-blur-sm"
          />

          <button
            onClick={() => setSignupMethod('email')}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            <Mail size={20} />
            Sign up with Email
          </button>
        </div>
      ) : (
        <form onSubmit={handleEmailSignup} className="space-y-6">
          <InputField
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            className="bg-white/5 border-white/10 focus:border-purple-500 focus:ring-purple-500/20"
          />

          {/* Password Input */}
          <div className="relative">
            <InputField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              className="bg-white/5 border-white/10 focus:border-purple-500 focus:ring-purple-500/20"
              icon={<Lock className="text-slate-400" size={18} />}
            />
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="absolute right-3 bottom-3 text-slate-400 hover:text-slate-200"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* Confirm Password Input */}
          <div className="relative">
            <InputField
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              className="bg-white/5 border-white/10 focus:border-purple-500 focus:ring-purple-500/20"
              icon={<Lock className="text-slate-400" size={18} />}
            />
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="absolute right-3 bottom-3 text-slate-400 hover:text-slate-200"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-3">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Creating account...
              </div>
            ) : (
              'Create Account'
            )}
          </button>

          <button
            onClick={() => {
              setSignupMethod(null);
              setEmail('');
              setPassword('');
              setConfirmPassword('');
              setError(null);
              setMessage(null);
            }}
            className="w-full text-sm text-slate-400 hover:text-slate-200 transition-colors"
            type="button"
          >
            Back to options
          </button>
        </form>
      )}

      <div className="mt-8 text-center text-sm">
        <p className="text-slate-400">
          Already have an account?{' '}
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('switchToLogin'))}
            className="text-purple-400 hover:text-purple-300 font-medium transition-colors bg-transparent border-none cursor-pointer"
          >
            Sign in
          </button>
        </p>
        <p className="text-slate-500 text-xs mt-2">
          By signing up, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};