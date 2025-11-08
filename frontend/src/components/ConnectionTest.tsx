import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export function ConnectionTest() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [backendInfo, setBackendInfo] = useState<any>(null);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const health = await apiService.healthCheck();
      setBackendInfo(health);
      setStatus('connected');
    } catch (error) {
      console.error('Backend connection failed:', error);
      setStatus('error');
    }
  };

  return (
    <div className="fixed bottom-4 right-4 bg-slate-800 rounded-lg p-4 shadow-xl border border-slate-700 max-w-sm">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${
          status === 'connected' ? 'bg-green-500' :
          status === 'error' ? 'bg-red-500' :
          'bg-yellow-500 animate-pulse'
        }`} />
        <div>
          <p className="text-white font-semibold text-sm">
            {status === 'connected' ? '✅ Backend Connected' :
             status === 'error' ? '❌ Backend Offline' :
             '⏳ Checking...'}
          </p>
          {backendInfo && (
            <p className="text-slate-400 text-xs mt-1">
              Version: {backendInfo.version} | Models: {backendInfo.features?.length || 0}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
