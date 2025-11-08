import { Sparkles, User } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

// Helper function to render content with images and audio
function renderContent(content: string) {
  // Check if content contains image markdown
  const imageMatch = content.match(/!\[.*?\]\((data:image\/[^)]+)\)/);
  if (imageMatch) {
    const imageData = imageMatch[1];
    const textBefore = content.substring(0, imageMatch.index);
    const textAfter = content.substring((imageMatch.index || 0) + imageMatch[0].length);
    
    return (
      <>
        {textBefore && <p className="mb-3">{textBefore}</p>}
        <img 
          src={imageData} 
          alt="Generated" 
          className="rounded-lg max-w-full h-auto shadow-lg"
          style={{ maxHeight: '512px' }}
        />
        {textAfter && <p className="mt-3">{textAfter}</p>}
      </>
    );
  }

  // Check if content contains audio HTML
  const audioMatch = content.match(/<audio[^>]*src="([^"]+)"[^>]*><\/audio>/);
  if (audioMatch) {
    const audioData = audioMatch[1];
    const textBefore = content.substring(0, audioMatch.index);
    const textAfter = content.substring((audioMatch.index || 0) + audioMatch[0].length);
    
    return (
      <>
        {textBefore && <p className="mb-3 whitespace-pre-wrap">{textBefore}</p>}
        <audio 
          controls 
          src={audioData}
          className="w-full max-w-md rounded-lg"
        />
        {textAfter && <p className="mt-3">{textAfter}</p>}
      </>
    );
  }

  // Regular text content
  return content;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isAssistant = role === 'assistant';

  return (
    <div
      className={`flex items-start gap-4 p-6 animate-fade-in-up ${
        isAssistant ? 'justify-start' : 'justify-end'
      }`}
    >
      {/* CoLab avatar on the left */}
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
          {isAssistant ? 'CoLab' : 'You'}
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
              ? '18px 18px 18px 0px' // CoLab (normal)
              : '18px 0px 18px 18px', // USER bubble (flat top-right corner)
          }}
        >
          {renderContent(content)}
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
