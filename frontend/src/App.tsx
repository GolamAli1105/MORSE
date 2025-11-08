import { useState, useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';
import LoadingScreen from './components/LoadingScreen';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import EmptyState from './components/EmptyState';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { AuthCallback } from './pages/AuthCallback';
import { ConnectionTest } from './components/ConnectionTest';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  category: string;
  messages: Message[];
  musicInputUnlocked?: boolean;
  selectedMusicOption?: string | null;
}

function App() {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('music');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [authPage, setAuthPage] = useState<'none' | 'login' | 'signup' | 'forgot-password'>('none');

  const [expandedInput, setExpandedInput] = useState(false); // design/writing input
  const [musicInputActive, setMusicInputActive] = useState(false); // music input
  const [resetTrigger, setResetTrigger] = useState(0); // triggers ChatInput reset

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  const handleLoadingComplete = () => setLoading(false);

  const handleNewChat = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: 'New Chat',
      category: selectedCategory,
      messages: [],
      musicInputUnlocked: selectedCategory !== 'music',
      selectedMusicOption: null,
    };

    setConversations(prev => [newConv, ...prev]);
    setCurrentConversationId(newConv.id);

    if (selectedCategory === 'music') {
      setMusicInputActive(true);
    } else {
      setExpandedInput(true);
    }
  };

  const simulateAIResponse = (content: string, category: string): string => {
    const responses = {
      music: [
        "Let's talk music! Ask about chords, scales, or any genre you like.",
        "Interesting! Music is a language of its own — let’s explore that.",
        "That’s a great question! Let’s dive into rhythm, harmony, or melody.",
      ],
      design: [
        "Design blends creativity and function — want to talk color or layout?",
        "Typography, grids, and color — the pillars of design!",
      ],
      writing: [
        "Writing is all about clarity and emotion — tell me your topic!",
        "Storytelling begins with characters and conflict — let’s shape it!",
      ],
    };
    const arr = responses[category as keyof typeof responses] || responses.writing;
    return arr[Math.floor(Math.random() * arr.length)];
  };

  // ---------------------------
  // Handle sending messages
  // ---------------------------
  const handleSendMessage = async (content: string) => {
    if (!currentConversationId || !user) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content };

    setConversations(prev =>
      prev.map(conv => {
        if (conv.id === currentConversationId) {
          const updatedMessages = [...conv.messages, userMessage];

          // Auto-update title if it's still default
          const updatedTitle =
            conv.title === 'New Chat' && updatedMessages.length === 1
              ? content
              : conv.title;

          return { ...conv, messages: updatedMessages, title: updatedTitle };
        }
        return conv;
      })
    );

    setIsTyping(true);

    try {
      // Map category to modality
      const modality = selectedCategory === 'music' ? 'music' : 
                       selectedCategory === 'design' ? 'image' : 'text';

      // Call the backend API
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          modality: modality,
          prompt: content,
          style: 'default',
          use_rag: false,
          parameters: modality === 'image' ? { num_inference_steps: 30 } : 
                      modality === 'music' ? { duration: 15 } : 
                      { max_length: 200 }
        }),
      });

      const data = await response.json();

      // Format the response based on modality
      let aiContent = '';
      if (modality === 'text') {
        aiContent = data.text || 'Generated text content';
      } else if (modality === 'image') {
        aiContent = `![Generated Image](data:image/png;base64,${data.image_data})`;
      } else if (modality === 'music') {
        aiContent = `🎵 Music generated successfully!\n\n<audio controls src="data:audio/wav;base64,${data.audio_data}"></audio>`;
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: aiContent,
      };

      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? { ...conv, messages: [...conv.messages, aiMessage] }
            : conv
        )
      );
    } catch (error) {
      console.error('Generation failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, generation failed. Please try again.',
      };
      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? { ...conv, messages: [...conv.messages, errorMessage] }
            : conv
        )
      );
    } finally {
      setIsTyping(false);
    }

    if (selectedCategory !== 'music') setExpandedInput(true);
  };

  // ---------------------------
  // Category selection
  // ---------------------------
  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category);
    if (category === 'music') {
      setMusicInputActive(false);
      setExpandedInput(false);
    } else {
      setExpandedInput(false);
      setMusicInputActive(false);
    }
  };

  const handleConversationSelect = (id: string) => {
    setCurrentConversationId(id);
    const conv = conversations.find(c => c.id === id);
    if (conv) {
      setSelectedCategory(conv.category);
      if (conv.category === 'music') {
        setMusicInputActive(conv.musicInputUnlocked ?? false);
        setExpandedInput(false);
      } else {
        setExpandedInput(conv.messages.length > 0);
        setMusicInputActive(false);
      }
    }
  };

  // ---------------------------
  // Suggestion click
  // ---------------------------
  const handleSuggestionClick = (suggestion: string, deselect = false) => {
    if (!currentConversationId) return;

    if (selectedCategory === 'music') {
      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? {
                ...conv,
                musicInputUnlocked: !deselect,
                selectedMusicOption: deselect ? null : suggestion,
              }
            : conv
        )
      );
      setMusicInputActive(!deselect);
    } else {
      handleSendMessage(suggestion);
    }
  };

  // ---------------------------
  // Delete conversation
  // ---------------------------
  const handleDeleteConversation = (id: string) => {
    setConversations(prev => {
      const updated = prev.filter(conv => conv.id !== id);

      // Trigger ChatInput reset
      setResetTrigger(prev => prev + 1);

      if (currentConversationId === id) {
        if (updated.length > 0) {
          const nextConv = updated[0];
          setCurrentConversationId(nextConv.id);
          setSelectedCategory(nextConv.category);

          if (nextConv.category === 'music') {
            setMusicInputActive(nextConv.musicInputUnlocked ?? false);
            setExpandedInput(false);
          } else {
            setExpandedInput(false);
            setMusicInputActive(false);
          }
        } else {
          setCurrentConversationId(null);
          if (selectedCategory === 'music') {
            setMusicInputActive(false);
          } else {
            setExpandedInput(false);
          }
        }
      }

      return updated;
    });
  };

  const handleRenameConversation = (id: string, newTitle: string) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === id ? { ...conv, title: newTitle } : conv
      )
    );
  };

  // ---------------------------
  // Initialize state
  // ---------------------------
  useEffect(() => {
    if (conversations.length === 0) {
      setCurrentConversationId(null);
      setMusicInputActive(false);
      setExpandedInput(false);
    }
  }, [conversations.length]);

  // ---------------------------
  // Handle auth page switching
  // ---------------------------
  useEffect(() => {
    const handleSwitchToLogin = () => {
      setAuthPage('login');
    };

    const handleSwitchToSignup = () => {
      setAuthPage('signup');
    };

    const handleSwitchToForgotPassword = () => {
      setAuthPage('forgot-password');
    };

    window.addEventListener('switchToLogin', handleSwitchToLogin);
    window.addEventListener('switchToSignup', handleSwitchToSignup);
    window.addEventListener('switchToForgotPassword', handleSwitchToForgotPassword);
    
    return () => {
      window.removeEventListener('switchToLogin', handleSwitchToLogin);
      window.removeEventListener('switchToSignup', handleSwitchToSignup);
      window.removeEventListener('switchToForgotPassword', handleSwitchToForgotPassword);
    };
  }, []);

  useEffect(() => {
    if (!authLoading) {
      if (user) {
        setAuthPage('none'); // ✅ hide auth screens when user logs in
      } else if (authPage === 'none') {
        setAuthPage('login'); // ✅ show login if not logged in
      }
    }
  }, [user, authLoading]);

  // Handle authentication states
  if (authLoading) {
    return <LoadingScreen onLoadingComplete={handleLoadingComplete} />;
  }

  // Handle auth callback and reset password routes
  if (window.location.pathname === '/auth/callback') return <AuthCallback />;
  if (window.location.pathname === '/auth/reset-password') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-3xl">
          <div className="bg-slate-800 rounded-2xl shadow-xl p-8">
            <ResetPasswordPage />
          </div>
        </div>
      </div>
    );
  }

  // Show auth pages when not authenticated
  if (!user && authPage !== 'none') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-3xl">
          <div className="bg-slate-800 rounded-2xl shadow-xl p-8">
            {authPage === 'login' && <LoginPage />}
            {authPage === 'signup' && <SignupPage />}
            {authPage === 'forgot-password' && <ForgotPasswordPage />}
          </div>
        </div>
      </div>
    );
  }

  if (authPage !== 'none') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-3xl">
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setAuthPage('none')}
              className="px-3 py-2 text-sm text-slate-400 hover:text-slate-200"
            >
              Close
            </button>
          </div>
          <div className="bg-slate-800 rounded-2xl shadow-xl p-8">
            {authPage === 'login' && <LoginPage />}
            {authPage === 'signup' && <SignupPage />}
            {authPage === 'forgot-password' && <ForgotPasswordPage />}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex overflow-hidden">
      <ConnectionTest />
      <Sidebar
        selectedCategory={selectedCategory}
        onCategorySelect={handleCategorySelect}
        conversations={conversations}
        onNewChat={handleNewChat}
        onConversationSelect={handleConversationSelect}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        currentConversationId={currentConversationId}
        onOpenAuth={setAuthPage}
      />

      <div className="flex-1 flex flex-col transition-all duration-300">
        <div className="flex-1 overflow-y-auto">
          {currentConversation ? (
            currentConversation.messages.length > 0 ? (
              <div className="max-w-4xl mx-auto">
                {currentConversation.messages.map(m => (
                  <ChatMessage key={m.id} role={m.role} content={m.content} />
                ))}
                {isTyping && (
                  <div className="flex gap-4 p-6 bg-slate-800/50">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-cyan-400">
                      <div className="w-5 h-5 flex gap-1 justify-center">
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-100"></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-200"></div>
                      </div>
                    </div>
                    <p className="text-slate-400 text-sm font-semibold">COSMOS</p>
                  </div>
                )}
              </div>
            ) : (
              <EmptyState
                category={selectedCategory}
                onSuggestionClick={handleSuggestionClick}
                selectedMusicOption={currentConversation.selectedMusicOption}
              />
            )
          ) : (
            <EmptyState
              category={selectedCategory}
              onSuggestionClick={handleSuggestionClick}
              selectedMusicOption={null}
            />
          )}
        </div>

        <ChatInput
          onSend={handleSendMessage}
          disabled={isTyping}
          category={selectedCategory}
          active={selectedCategory === 'music' ? musicInputActive : undefined}
          resetTrigger={resetTrigger}
        />
      </div>
    </div>
  );
}

export default App;
