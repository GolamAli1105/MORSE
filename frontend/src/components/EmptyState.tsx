import { Music, Palette, PenTool, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  category: string;
  onSuggestionClick: (suggestion: string, deselect?: boolean) => void; // ✅ support deselect
  selectedMusicOption?: string | null;
}

export default function EmptyState({
  category,
  onSuggestionClick,
  selectedMusicOption,
}: EmptyStateProps) {
  const content = {
    music: {
      icon: Music,
      color: 'text-pink-400',
      title: 'Music Assistant',
      suggestions: ['Lyrics to Music', 'Prompt to Music'],
    },
    design: {
      icon: Palette,
      color: 'text-cyan-400',
      title: 'Design Assistant',
      suggestions: [
        'Explain the principles of good UI design',
        'How do I choose a color palette?',
        'What are current design trends?',
        'Tips for creating a logo',
      ],
    },
    writing: {
      icon: PenTool,
      color: 'text-green-400',
      title: 'Writing Assistant',
      suggestions: [
        'Help me brainstorm story ideas',
        'How to write compelling characters',
        'Tips for improving my writing style',
        'Structure for a blog post',
      ],
    },
  };

  const current = content[category as keyof typeof content];
  const Icon = current.icon;

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-3xl w-full space-y-8 animate-fade-in">
        <div className="text-center">
          <div className="relative inline-block mb-6">
            <Icon className={`w-20 h-20 ${current.color} mx-auto animate-float`} />
            <div className="absolute inset-0 blur-2xl opacity-30 bg-blue-500"></div>
          </div>
          <h2 className="text-4xl font-bold text-white mb-2">
            COSMOS {current.title}
          </h2>
          <p className="text-slate-400">
            Ask me anything about {category}. I'm here to help!
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {current.suggestions.map((suggestion, index) => {
            const isSelected =
              category === 'music' && selectedMusicOption === suggestion;

            return (
              <button
                key={index}
                onClick={() => {
                  if (category === 'music' && isSelected) {
                    // ✅ deselect if same button clicked again
                    onSuggestionClick(suggestion, true);
                  } else {
                    onSuggestionClick(suggestion);
                  }
                }}
                className={`border rounded-xl p-4 text-left transition-all duration-200 group
                  ${
                    isSelected
                      ? 'bg-blue-600/60 border-blue-400 scale-105 shadow-lg shadow-blue-500/40'
                      : 'bg-slate-800/50 hover:bg-slate-800 border-slate-700 hover:border-slate-600 hover:scale-105'
                  }`}
              >
                <div className="flex items-start gap-3">
                  <Sparkles
                    className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                      isSelected
                        ? 'text-white animate-pulse'
                        : 'text-blue-400 group-hover:animate-pulse'
                    }`}
                  />
                  <span
                    className={`text-sm ${
                      isSelected ? 'text-white font-semibold' : 'text-slate-300'
                    }`}
                  >
                    {suggestion}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
