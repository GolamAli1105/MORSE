import { ReactNode } from 'react';

interface SocialButtonProps {
  icon: ReactNode;
  text: string;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}

export function SocialButton({ icon, text, onClick, disabled, className = '' }: SocialButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full flex items-center justify-center gap-3 px-6 py-4 border rounded-xl transition-all duration-200 font-semibold text-base disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {icon}
      <span className="text-white">{text}</span>
    </button>
  );
}
