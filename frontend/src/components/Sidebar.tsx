import {
  Music,
  Palette,
  PenTool,
  Plus,
  MessageSquare,
  User,
  LogIn,
  Sparkles,
  ChevronDown,
  Menu,
  ChevronLeft,
  MoreHorizontal,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProfileModal from './ProfileModal';

interface Conversation {
  id: string;
  title: string;
  category: string;
}

interface SidebarProps {
  selectedCategory: string;
  onCategorySelect: (category: string) => void;
  conversations: Conversation[];
  onNewChat: () => void;
  onConversationSelect: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  currentConversationId: string | null;
  onOpenAuth?: (page: 'login' | 'signup') => void;
}

export default function Sidebar({
  selectedCategory,
  onCategorySelect,
  conversations,
  onNewChat,
  onConversationSelect,
  onDeleteConversation,
  onRenameConversation,
  currentConversationId,
  onOpenAuth,
}: SidebarProps) {
  const [showCategories, setShowCategories] = useState(true);
  const [showChats, setShowChats] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const { user } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  // ✅ Track which conversation is being edited
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [tempTitle, setTempTitle] = useState('');

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  const categories = [
    { id: 'music', label: 'Music', icon: Music, color: 'text-pink-400' },
    { id: 'design', label: 'Design', icon: Palette, color: 'text-cyan-400' },
    { id: 'writing', label: 'Writing', icon: PenTool, color: 'text-green-400' },
  ];

  return (
    <>
      {/* Floating reopen button */}
      {!isSidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed top-5 left-5 z-50 bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 p-2 rounded-lg transition-colors shadow-lg"
          title="Open Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
      )}

      {/* Sidebar container */}
      <div
        className={`fixed md:static top-0 left-0 h-full z-40 transform transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } w-64 bg-slate-900 border-r border-slate-800 flex flex-col`}
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Sparkles className="w-6 h-6 text-blue-400 animate-pulse-slow" />
                <div className="absolute inset-0 blur-lg bg-blue-500 opacity-30"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">COSMOS</h1>
                <p className="text-xs text-slate-400">AI Assistant</p>
              </div>
            </div>

            <button
              onClick={toggleSidebar}
              className="text-slate-400 hover:text-white transition-colors hover:bg-slate-800 p-2 rounded-lg flex-shrink-0"
              title="Close Sidebar"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat button */}
          <button
            onClick={onNewChat}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-3 flex items-center justify-center gap-2 transition-all duration-200 hover:scale-105"
          >
            <Plus className="w-5 h-5" />
            New Chat
          </button>
        </div>

        {/* Categories */}
        <div className="p-4 border-b border-slate-800">
          <div
            className="flex items-center justify-between cursor-pointer mb-3"
            onClick={() => setShowCategories(!showCategories)}
          >
            <h3 className="text-slate-400 text-xs font-semibold uppercase">Categories</h3>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform ${
                showCategories ? 'rotate-180' : ''
              }`}
            />
          </div>

          {showCategories && (
            <div className="space-y-2">
              {categories.map((category) => {
                const Icon = category.icon;
                const isActive = selectedCategory === category.id;
                return (
                  <button
                    key={category.id}
                    onClick={() => onCategorySelect(category.id)}
                    className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-slate-800 text-white'
                        : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? category.color : ''}`} />
                    <span>{category.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Chats */}
        <div className="flex-1 overflow-y-auto p-4 border-t border-slate-800">
          <div
            className="flex items-center justify-between cursor-pointer mb-3"
            onClick={() => setShowChats(!showChats)}
          >
            <h3 className="text-slate-400 text-xs font-semibold uppercase">Recent Chats</h3>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform ${
                showChats ? 'rotate-180' : ''
              }`}
            />
          </div>

          {showChats && (
            <div className="space-y-1">
              {conversations.map((conv) => {
                const isEditing = editingConversationId === conv.id;

                return (
                  <div
                    key={conv.id}
                    className={`relative w-full flex items-center justify-between px-2 py-1 rounded-lg transition-all duration-200 group ${
                      currentConversationId === conv.id
                        ? 'bg-slate-800 text-white'
                        : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                    }`}
                  >
                    <button
                      onClick={() => onConversationSelect(conv.id)}
                      className="flex items-center gap-2 truncate flex-1 text-left px-2 py-2"
                    >
                      <MessageSquare className="w-4 h-4 flex-shrink-0" />
                      {isEditing ? (
                        <input
                          value={tempTitle}
                          onChange={(e) => setTempTitle(e.target.value)}
                          onBlur={() => {
                            if (tempTitle.trim() !== '')
                              onRenameConversation(conv.id, tempTitle.trim());
                            setEditingConversationId(null);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && tempTitle.trim() !== '') {
                              onRenameConversation(conv.id, tempTitle.trim());
                              setEditingConversationId(null);
                            }
                            if (e.key === 'Escape') setEditingConversationId(null);
                          }}
                          autoFocus
                          className="w-full bg-slate-700 text-white rounded px-2 py-1 text-sm"
                        />
                      ) : (
                        <span
                          onDoubleClick={() => {
                            setEditingConversationId(conv.id);
                            setTempTitle(conv.title);
                          }}
                          className="truncate text-sm cursor-pointer"
                        >
                          {conv.title}
                        </span>
                      )}
                    </button>

                    {/* 3-dot menu */}
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenMenuId(openMenuId === conv.id ? null : conv.id);
                        }}
                        className="p-2 rounded-md opacity-0 group-hover:opacity-100 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </button>

                      {openMenuId === conv.id && (
                        <div
                          className="absolute right-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-lg flex items-center gap-2 px-2 py-1 z-50"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() => {
                              setEditingConversationId(conv.id);
                              setTempTitle(conv.title);
                              setOpenMenuId(null);
                            }}
                            className="text-xs text-blue-400 hover:text-blue-300 px-2 py-1 rounded transition-colors"
                          >
                            Rename
                          </button>
                          <button
                            onClick={() => {
                              onDeleteConversation(conv.id);
                              setOpenMenuId(null);
                            }}
                            className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {conversations.length === 0 && (
                <p className="text-xs text-slate-500 text-center mt-2">
                  No chats yet. Start a new one!
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800">
          {user ? (
            <div className="flex items-center justify-between">
              <div
                className="flex items-center gap-3 flex-1 cursor-pointer"
                onClick={() => setShowProfile(true)}
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-full flex items-center justify-center">
                  {user.user_metadata?.full_name ? (
                    <span className="text-white font-semibold text-sm">
                      {user.user_metadata.full_name
                        .split(' ')
                        .map((n: string) => n[0])
                        .slice(0, 2)
                        .join('')}
                    </span>
                  ) : (
                    <User className="w-5 h-5 text-white" />
                  )}
                </div>
                <div className="min-w-0">
                  <p className="text-white text-sm font-semibold truncate">
                    {user.user_metadata?.full_name || user.email || 'User'}
                  </p>
                  <p className="text-slate-400 text-xs truncate">{user.email || ''}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <button
                onClick={() => onOpenAuth?.('login')}
                className="w-full bg-slate-800 hover:bg-slate-700 text-white rounded-lg px-4 py-3 flex items-center justify-center gap-2 transition-all duration-200"
              >
                <LogIn className="w-5 h-5" />
                Login
              </button>
              <button
                onClick={() => onOpenAuth?.('signup')}
                className="w-full bg-slate-800/90 hover:bg-slate-700 text-white rounded-lg px-4 py-3 flex items-center justify-center gap-2 transition-all duration-200"
              >
                <User className="w-5 h-5" />
                Sign Up
              </button>
            </div>
          )}
        </div>

        {/* Profile Modal */}
        <ProfileModal open={showProfile} onClose={() => setShowProfile(false)} />
      </div>
    </>
  );
}
