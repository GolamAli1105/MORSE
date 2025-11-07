import { ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="w-full flex items-center justify-center relative overflow-hidden 
                    bg-gradient-to-br from-[#030617] via-[#0F1B4C] to-[#1E40AF] text-white py-20">

      {/* Soft Background Glow Effects */}
      <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-blue-700/30 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-indigo-600/25 rounded-full blur-[140px]"></div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0A112F]/30 to-[#0F1B4C]/70"></div>

      {/* Center Card */}
      <div className="relative z-10 w-full max-w-md px-6 py-8 
                      bg-gradient-to-br from-[#101935] via-[#12224A] to-[#1E3A8A]
                      border border-blue-500/20 
                      rounded-2xl shadow-[0_8px_50px_rgba(30,64,175,0.4)]
                      backdrop-blur-xl">
        {children}
      </div>
    </div>
  );
}
