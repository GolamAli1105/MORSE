import { } from 'react';
import { User as UserIcon, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface ProfileModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ProfileModal({ open, onClose }: ProfileModalProps) {
  const { user, signOut } = useAuth();

  if (!open) return null;

  const name = user?.user_metadata?.full_name || user?.user_metadata?.name || '';
  const email = user?.email || '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-md mx-4 bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
            {name ? (
              <span className="text-white font-semibold">
                {name.split(' ').map((n: string) => n[0]).slice(0,2).join('')}
              </span>
            ) : (
              <UserIcon className="w-6 h-6 text-white" />
            )}
          </div>
          <div>
            <p className="text-slate-900 font-semibold">{name || 'User'}</p>
            <p className="text-slate-500 text-sm truncate">{email}</p>
          </div>
        </div>

        <div className="space-y-3">
          <button
            onClick={async () => {
              await signOut();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>

          <button
            onClick={onClose}
            className="w-full px-4 py-2 border rounded-lg text-sm text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
