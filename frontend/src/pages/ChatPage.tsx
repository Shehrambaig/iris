import { useState, useRef, useEffect } from 'react';
import { Sparkles, Plus, ArrowUp, Home, MessageSquare, FileText, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Source {
  title: string;
  url: string;
  content: string;
  score: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

interface ChatPageProps {
  symbol?: string;
}

export const ChatPage = ({ symbol }: ChatPageProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          symbol: symbol,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: data.answer || 'Sorry, I could not generate a response.',
        timestamp: new Date(),
        sources: data.sources || []
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    setMessages([]);
    try {
      await fetch(`http://localhost:8000/api/rag/clear-history?session_id=${sessionId}`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error clearing chat history on backend:', error);
    }
  };

  const renderMessageContent = (content: string, sources?: Source[]) => {
    // Regex for markdown links: [text](url)
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    // Regex for Source citations: (Source N) or [Source N]
    const sourceRegex = /(\(Source \d+\)|\[Source \d+\])/g;

    // Split content by links first
    const parts = content.split(linkRegex);

    // If no links, process for sources normally
    if (parts.length === 1) {
      return (
        <p className="text-[15px] leading-7 text-gray-100 whitespace-pre-wrap">
          {processSourceCitations(content, sources)}
        </p>
      );
    }

    // Reassemble with links
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    // reset regex
    linkRegex.lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
      // Push text before link (processed for sources)
      if (match.index > lastIndex) {
        const textBefore = content.substring(lastIndex, match.index);
        elements.push(processSourceCitations(textBefore, sources));
      }

      // Push link
      elements.push(
        <a
          key={match.index}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline underline-offset-2 mx-1 font-medium"
        >
          {match[1]}
        </a>
      );

      lastIndex = linkRegex.lastIndex;
    }

    // Push remaining text
    if (lastIndex < content.length) {
      elements.push(processSourceCitations(content.substring(lastIndex), sources));
    }

    return <p className="text-[15px] leading-7 text-gray-100 whitespace-pre-wrap">{elements}</p>;
  };

  const processSourceCitations = (text: string, sources?: Source[]) => {
    if (!sources || sources.length === 0) return text;

    const parts = text.split(/(\(Source \d+\)|\[Source \d+\])/g);

    return parts.map((part, index) => {
      const match = part.match(/(?:Source )(\d+)/);
      if (match) {
        const sourceIndex = parseInt(match[1]) - 1;
        const source = sources[sourceIndex];

        if (source) {
          return (
            <button
              key={`${index}-${sourceIndex}`}
              onClick={() => setSelectedSource(source)}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-1 rounded bg-blue-500/20 hover:bg-blue-500/40 text-blue-300 hover:text-blue-200 text-xs font-medium transition-colors cursor-pointer border border-blue-500/30 align-middle"
              title={source.title}
            >
              <FileText className="w-3 h-3" />
              {part.replace(/[()\[\]]/g, '')}
            </button>
          );
        }
      }
      return part;
    });
  };

  const chatHistory = [
    "Apple Earnings Q3 Analysis",
    "Tesla Stock Predictions",
    "NVIDIA Growth Metrics",
    "Market Trends Discussion",
    "Amazon Revenue Report",
  ];

  return (
    <div className="flex h-screen w-screen bg-gradient-to-b from-[#0a0e27] to-[#0f1420] overflow-hidden text-white">

      {/* MINIMAL LEFT SIDEBAR - Claude Style */}
      <div className="w-16 bg-[#0a0e27]/50 border-r border-[#1e222d]/50 flex flex-col items-center py-4 gap-3 shrink-0">

        {/* Animated Logo */}
        <div className="logo-container mb-2">
          <div className="logo-line logo-line-1"></div>
          <div className="logo-line logo-line-2"></div>
          <div className="logo-line logo-line-3"></div>
          <div className="logo-line logo-line-4"></div>
          <div className="logo-line logo-line-5"></div>
        </div>

        {/* New Chat Button - Minimal */}
        <button
          onClick={handleNewChat}
          className="w-10 h-10 rounded-lg bg-[#1a1f3a]/60 hover:bg-[#1a1f3a] border border-[#1e222d] hover:border-blue-500/30 flex items-center justify-center transition-all group"
          title="New Chat"
        >
          <Plus className="w-5 h-5 text-gray-400 group-hover:text-white" strokeWidth={2} />
        </button>

        {/* Chat History Icon - Opens History */}
        <button
          onClick={() => setShowHistory(!showHistory)}
          className={`w-10 h-10 rounded-lg ${showHistory ? 'bg-[#1a1f3a]' : 'bg-[#1a1f3a]/60'} hover:bg-[#1a1f3a] border border-[#1e222d] hover:border-blue-500/30 flex items-center justify-center transition-all group`}
          title="Chat History"
        >
          <MessageSquare className={`w-5 h-5 ${showHistory ? 'text-blue-400' : 'text-gray-400'} group-hover:text-blue-400`} strokeWidth={2} />
        </button>
      </div>

      {/* Chat History Sidebar - Appears when clicked */}
      {showHistory && (
        <div className="w-64 bg-[#0a0e27] border-r border-[#1e222d] flex flex-col shrink-0 animate-slide-in">
          <div className="p-4">
            <input
              type="text"
              placeholder="Search chats..."
              className="w-full px-3 py-2 bg-[#1a1f3a]/60 border border-[#1e222d] rounded-lg text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500/50 transition-all"
            />
          </div>
          <div className="flex-1 overflow-y-auto px-2 custom-scrollbar">
            <div className="space-y-1">
              {chatHistory.map((chat, i) => (
                <button
                  key={i}
                  className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-[#1a1f3a]/80 text-sm text-gray-400 hover:text-white transition-all truncate"
                >
                  {chat}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col h-full relative min-w-0">

        {/* Home Button - Top Right */}
        <div className="absolute top-4 right-4 z-50">
          <button
            onClick={() => navigate('/')}
            className="p-2.5 bg-[#1a1f3a]/60 hover:bg-[#1a1f3a] rounded-lg border border-[#1e222d] hover:border-blue-500/30 transition-all group"
          >
            <Home className="w-5 h-5 text-gray-400 group-hover:text-white" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="max-w-4xl px-8 w-full h-full flex flex-col" style={{ marginLeft: 'auto', marginRight: 'auto', transform: 'translateX(16px)' }}>

            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex items-center justify-center mb-8 shadow-xl">
                  <Sparkles className="w-8 h-8 text-blue-400" />
                </div>
                <h1 className="text-3xl font-semibold text-white">How can I help you today?</h1>
              </div>
            ) : (
              <div className="py-16 pb-8">
                {messages.map((message) => (
                  <div key={message.id} className={`mb-8 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>

                    {message.role === 'assistant' ? (
                      <div className="flex gap-4 max-w-[80%]">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex-shrink-0 flex items-center justify-center shadow-lg">
                          <Sparkles className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="flex-1 pt-1">
                          {renderMessageContent(message.content, message.sources)}
                        </div>
                      </div>
                    ) : (
                      <div className="flex gap-4 max-w-[80%] flex-row-reverse">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500/20 to-green-600/20 border border-emerald-500/30 flex-shrink-0 flex items-center justify-center shadow-lg">
                          <span className="text-sm font-semibold text-emerald-400">U</span>
                        </div>
                        <div className="flex-1 pt-1 text-right">
                          <p className="text-[15px] leading-7 text-gray-100">{message.content}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Morphing Shape Loading Animation */}
                {isLoading && (
                  <div className="mb-8 flex justify-start">
                    <div className="flex gap-4 max-w-[80%]">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex-shrink-0 flex items-center justify-center shadow-lg">
                        <Sparkles className="w-5 h-5 text-blue-400" />
                      </div>
                      <div className="flex-1 pt-2">
                        {/* Animated Lines */}
                        <div className="lines-container">
                          <div className="line line-1"></div>
                          <div className="line line-2"></div>
                          <div className="line line-3"></div>
                          <div className="line line-4"></div>
                          <div className="line line-5"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input Area - Centered */}
        <div className="shrink-0 w-full bg-gradient-to-t from-[#0a0e27] via-[#0a0e27]/95 to-transparent pb-8 pt-6">
          <div className="max-w-5xl px-8" style={{ marginLeft: 'auto', marginRight: 'auto', transform: 'translateX(16px)' }}>
            <form onSubmit={handleSubmit}>
              <div className="relative flex items-center gap-3 bg-[#1a1f3a]/60 border border-[#1e222d] rounded-[28px] px-5 py-3 focus-within:border-blue-500/50 transition-all shadow-2xl">

                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  placeholder="Message AI Analyst..."
                  disabled={isLoading}
                  rows={1}
                  className="flex-1 bg-transparent text-white placeholder-gray-500 resize-none outline-none max-h-[200px] overflow-y-auto custom-scrollbar text-[15px]"
                  style={{ minHeight: '48px', paddingTop: '14px', paddingBottom: '10px', paddingLeft: '4px' }}
                />

                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all ${input.trim() && !isLoading
                    ? 'bg-white text-black hover:bg-gray-100 shadow-lg'
                    : 'bg-[#2a2e39] text-gray-600 cursor-not-allowed'
                    }`}
                  style={{ marginRight: '2px' }}
                >
                  <ArrowUp className="w-5 h-5" strokeWidth={2.5} />
                </button>
              </div>
            </form>

            <div className="text-center mt-3">
              <p className="text-xs text-gray-500">AI can make mistakes. Check important info.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Source Detail Modal */}
      {selectedSource && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in" onClick={() => setSelectedSource(null)}>
          <div className="bg-[#1a1f3a] border border-[#2e3547] rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-[#2e3547]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{selectedSource.title}</h3>
                  <p className="text-xs text-gray-400">Relevance Score: {(selectedSource.score * 100).toFixed(1)}%</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="p-1 hover:bg-[#2e3547] rounded-lg transition-colors text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar">
              <div className="prose prose-invert max-w-none">
                <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{selectedSource.content}</p>
              </div>
            </div>
            <div className="p-4 border-t border-[#2e3547] bg-[#121623] rounded-b-xl flex justify-end">
              <button
                onClick={() => setSelectedSource(null)}
                className="px-4 py-2 bg-[#2e3547] hover:bg-[#3e475e] text-white rounded-lg text-sm font-medium transition-colors"
              >
                Close Header
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #2a2e39;
          border-radius: 20px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: #4b5563;
        }

        @keyframes slide-in {
          from {
            transform: translateX(-100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }

        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }

        /* Premium Animated Lines */
        .lines-container {
          display: flex;
          align-items: flex-end;
          justify-content: center;
          gap: 10px;
          height: 60px;
          padding: 10px 0;
        }

        .line {
          width: 3px;
          border-radius: 2px;
          position: relative;
          animation: line-bounce 2s ease-in-out infinite;
        }

        /* Individual line styles with different colors and delays */
        .line-1 {
          height: 30px;
          background: linear-gradient(180deg, rgba(59, 130, 246, 0.8), rgba(59, 130, 246, 1));
          filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.7));
          animation-delay: 0s;
        }

        .line-2 {
          height: 40px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.8), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.7));
          animation-delay: 0.2s;
        }

        .line-3 {
          height: 50px;
          background: linear-gradient(180deg, rgba(99, 102, 241, 0.8), rgba(99, 102, 241, 1));
          filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.7));
          animation-delay: 0.4s;
        }

        .line-4 {
          height: 35px;
          background: linear-gradient(180deg, rgba(139, 92, 246, 0.8), rgba(139, 92, 246, 1));
          filter: drop-shadow(0 0 4px rgba(139, 92, 246, 0.7));
          animation-delay: 0.6s;
        }

        .line-5 {
          height: 45px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.8), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.7));
          animation-delay: 0.8s;
        }

        @keyframes line-bounce {
          0%, 100% {
            transform: scaleY(1) translateY(0);
            opacity: 0.8;
          }
          50% {
            transform: scaleY(1.3) translateY(-5px);
            opacity: 1;
          }
        }

        /* Premium Animated Logo */
        .logo-container {
          display: flex;
          align-items: flex-end;
          justify-content: center;
          gap: 4px;
          height: 40px;
          width: 40px;
          padding: 5px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.15), transparent 70%);
          border-radius: 10px;
          position: relative;
        }

        .logo-container::before {
          content: '';
          position: absolute;
          inset: -10px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent 60%);
          border-radius: 20px;
          filter: blur(15px);
          animation: pulse-logo 3s ease-in-out infinite;
          z-index: -1;
        }

        .logo-line {
          width: 2px;
          border-radius: 1px;
          position: relative;
          animation: logo-bounce 2s ease-in-out infinite;
        }

        .logo-line-1 {
          height: 12px;
          background: linear-gradient(180deg, rgba(59, 130, 246, 0.9), rgba(59, 130, 246, 1));
          filter: drop-shadow(0 0 3px rgba(59, 130, 246, 0.8));
          animation-delay: 0s;
        }

        .logo-line-2 {
          height: 18px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.15s;
        }

        .logo-line-3 {
          height: 24px;
          background: linear-gradient(180deg, rgba(99, 102, 241, 0.9), rgba(99, 102, 241, 1));
          filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.9));
          animation-delay: 0.3s;
        }

        .logo-line-4 {
          height: 16px;
          background: linear-gradient(180deg, rgba(139, 92, 246, 0.9), rgba(139, 92, 246, 1));
          filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.8));
          animation-delay: 0.45s;
        }

        .logo-line-5 {
          height: 20px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.6s;
        }

        @keyframes logo-bounce {
          0%, 100% {
            transform: scaleY(1) translateY(0);
            opacity: 0.85;
          }
          50% {
            transform: scaleY(1.2) translateY(-2px);
            opacity: 1;
          }
        }

        @keyframes pulse-logo {
          0%, 100% {
            opacity: 0.6;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.1);
          }
        }
      `}</style>
    </div>
  );
};
