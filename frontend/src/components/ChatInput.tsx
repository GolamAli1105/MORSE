import { useState, useEffect } from 'react';
import { Send, Loader2, Mic } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  category: string;
  active?: boolean; // controlled by App for music
  resetTrigger?: number; // changes when chat is deleted
}

export default function ChatInput({
  onSend,
  disabled,
  category,
  active = true,
  resetTrigger = 0,
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [isActive, setIsActive] = useState(active);

  // Update isActive when parent changes (for music)
  useEffect(() => {
    if (category === 'music') {
      setIsActive(active);
    } else {
      setIsActive(true); // always active for design/writing
    }
  }, [category, active]);

  // Reset on chat delete or resetTrigger
  useEffect(() => {
    setInput('');
    setExpanded(false);
    if (category === 'music') {
      setIsActive(false); // collapsed and inactive
    } else {
      setIsActive(true); // active but collapsed
    }
  }, [resetTrigger, category]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled && isActive) {
      onSend(input);
      setInput('');
      if (category !== 'music') {
        setExpanded(true); // keep expanded for design/writing after sending
      }
    }
  };

  const placeholders = {
    music: 'Ask about music theory, composition, or recommendations...',
    design: 'Ask about design principles, color theory, or UI/UX...',
    writing: 'Ask about writing techniques, storytelling, or content creation...',
  };

  const handleClick = () => {
    if (!disabled && isActive) {
      setExpanded(true);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <div className="max-w-4xl mx-auto relative flex justify-center">
        <div
          className={`flex items-center border border-slate-700/70 bg-slate-800/50 rounded-full transition-all duration-300 ease-in-out overflow-hidden backdrop-blur-sm ${
            expanded
              ? 'w-full max-w-2xl px-4 py-2'
              : 'w-48 h-14 justify-between px-4 hover:scale-105 hover:border-blue-500/60 hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] cursor-pointer'
          }`}
          onClick={handleClick}
        >
          {!expanded ? (
            <>
              <span
                className={`text-white font-medium select-none ${
                  !isActive ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Ask COSMOS
              </span>
              <button
                type="button"
                disabled={!isActive}
                onClick={handleClick}
                className={`${
                  !isActive
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                } rounded-full p-3 transition-all duration-200 hover:scale-110`}
              >
                <Send className="w-4 h-4" />
              </button>
            </>
          ) : (
            <>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  placeholders[category as keyof typeof placeholders] ||
                  'Type your message...'
                }
                disabled={disabled || !isActive}
                className="flex-1 bg-transparent text-white placeholder-slate-400 px-2 focus:outline-none"
                autoFocus
              />
              <button
                type="button"
                className="p-3 text-slate-300 hover:text-white transition-colors duration-200"
                title="Voice input"
                disabled={!isActive}
              >
                <Mic className="w-5 h-5" />
              </button>
              <button
                type="submit"
                disabled={disabled || !input.trim() || !isActive}
                className="ml-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-full p-3 transition-all duration-200 hover:scale-105 disabled:hover:scale-100"
              >
                {disabled ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </form>
  );
}
