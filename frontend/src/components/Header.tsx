import { Menu } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="bg-slate-900/80 backdrop-blur-lg border-b border-slate-800 px-6 py-4 sticky top-0 z-10">
      <div className="flex items-center">
        <button
          onClick={onMenuClick}
          className="md:hidden text-slate-400 hover:text-white transition-colors"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>
    </header>
  );
}
