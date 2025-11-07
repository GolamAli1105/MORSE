import { Sparkles, User } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isAssistant = role === 'assistant';

  return (
    <div
      className={`flex items-start gap-4 p-6 animate-fade-in-up ${
        isAssistant ? 'justify-start' : 'justify-end'
      }`}
    >
      {/* COSMOS avatar on the left */}
      {isAssistant && (
        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-cyan-400 flex-shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
      )}

      {/* Message container */}
      <div
        className={`flex flex-col ${
          isAssistant ? 'items-start' : 'items-end'
        } max-w-[80%]`}
      >
        <p className="text-slate-400 text-sm font-semibold mb-1">
          {isAssistant ? 'COSMOS' : 'You'}
        </p>

        <div
          className={`leading-relaxed whitespace-pre-wrap break-words text-left px-4 py-2 text-[15px] ${
            isAssistant
              ? 'text-slate-200'
              : 'text-white bg-slate-700/40 backdrop-blur-sm'
          }`}
          style={{
            wordBreak: 'break-word',
            overflowWrap: 'break-word',
            whiteSpace: 'pre-wrap',
            borderRadius: isAssistant
              ? '18px 18px 18px 0px' // COSMOS (normal)
              : '18px 0px 18px 18px', // USER bubble (flat top-right corner)
          }}
        >
          {content}
        </div>
      </div>

      {/* User avatar on the right */}
      {!isAssistant && (
        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-slate-700 flex-shrink-0">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
}
