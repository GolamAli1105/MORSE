import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

interface LoadingScreenProps {
  onLoadingComplete: () => void;
}

export default function LoadingScreen({ onLoadingComplete }: LoadingScreenProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onLoadingComplete, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 30);

    return () => clearInterval(interval);
  }, [onLoadingComplete]);

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center z-50">
      <div className="text-center">
        <div className="relative mb-8">
          <div className="animate-pulse-slow">
            <Sparkles className="w-24 h-24 text-blue-400 mx-auto animate-spin-slow" />
          </div>
          <div className="absolute inset-0 blur-3xl bg-blue-500 opacity-30 animate-pulse"></div>
        </div>

        <h1 className="text-6xl font-bold text-white mb-4 animate-fade-in">
          COSMOS
        </h1>

        <p className="text-blue-300 text-lg mb-8 animate-fade-in-delay">
          Initializing AI Assistant...
        </p>

        <div className="w-64 h-2 bg-slate-800 rounded-full overflow-hidden mx-auto">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-300 ease-out rounded-full"
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        <p className="text-slate-400 text-sm mt-4">{progress}%</p>
      </div>
    </div>
  );
}
