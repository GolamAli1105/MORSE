import { InputHTMLAttributes } from 'react';

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  className?: string;
  icon?: React.ReactNode;
}

export function InputField({ label, error, className = '', ...props }: InputFieldProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">
        {label}
      </label>
      <input
        {...props}
        className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all bg-white/5 text-white placeholder-slate-400 ${className}`}
      />
      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
