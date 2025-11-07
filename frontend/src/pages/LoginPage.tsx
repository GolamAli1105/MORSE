import React, { useState } from 'react';
import { FcGoogle } from 'react-icons/fc';
import { InputField } from '../auth/InputField';
import { Divider } from '../auth/Divider';
import { SocialButton } from '../auth/SocialButton';
import { useAuth } from '../contexts/AuthContext';
import { Eye, EyeOff } from 'lucide-react';

export const LoginPage = () => {
  const { signIn, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rememberMe, setRememberMe] = useState(false);

  const togglePasswordVisibility = () => setShowPassword(!showPassword);

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const { error } = await signInWithGoogle();
      if (error) setError(error.message);
    } catch {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!email.trim() && !password.trim()) {
      setError('Please enter your email and password');
      setLoading(false);
      return;
    }

    if (!email.trim()) {
      setError('Please enter your email address');
      setLoading(false);
      return;
    }

    if (!password.trim()) {
      setError('Please enter your password');
      setLoading(false);
      return;
    }

    if (!email.includes('@') || !email.includes('.')) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const { error } = await signIn(email, password);
      if (error) setError(error.message);
    } catch {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">Welcome Back</h1>
        <p className="text-slate-400 text-lg">Sign in to continue to your account</p>
      </div>

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

      <div className="space-y-4 mb-6">
        <SocialButton
          icon={<FcGoogle size={24} />}
          text="Continue with Google"
          onClick={handleGoogleLogin}
          disabled={loading}
          className="bg-white/10 hover:bg-white/20 border border-white/20 backdrop-blur-sm"
        />
      </div>

      <Divider />

      <form onSubmit={handleEmailLogin} className="space-y-6 relative">
        <div className="space-y-4">
          <InputField
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            disabled={loading}
            required
            className="bg-white/5 border-white/10 focus:border-blue-500 focus:ring-blue-500/20"
          />

          {/* ✅ FIXED WRAPPER */}
          <div className="relative">
            <InputField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Enter your password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              disabled={loading}
              required
              className="bg-white/5 border-white/10 focus:border-blue-500 focus:ring-blue-500/20 pr-10"
            />
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="absolute right-3 bottom-3 text-slate-400 hover:text-slate-200"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800 transition-colors"
            />
            <span className="text-slate-300 group-hover:text-white transition-colors">Remember me</span>
          </label>
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('switchToForgotPassword'))}
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors bg-transparent border-none cursor-pointer"
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          disabled={loading || !email || !password}
          className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transform hover:-translate-y-0.5"
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Signing in...
            </div>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      <div className="mt-8 text-center text-sm">
        <p className="text-slate-400">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('switchToSignup'))}
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors bg-transparent border-none cursor-pointer"
          >
            Create account
          </button>
        </p>
      </div>
    </div>
  );
};

