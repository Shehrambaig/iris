import { Link, useLocation } from 'react-router-dom';
import { BarChart3, MessageSquare } from 'lucide-react';

export const Navigation = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="fixed top-20 right-6 z-50 flex flex-col gap-2">
      <Link
        to="/"
        className={`group relative p-3 rounded-xl transition-all shadow-lg backdrop-blur-sm border ${
          isActive('/')
            ? 'bg-gradient-to-br from-blue-500 to-indigo-600 border-blue-500/50 shadow-blue-500/30'
            : 'bg-[#1a1f3a]/80 border-[#1e222d] hover:border-[#2962FF]/50 hover:bg-[#1a1f3a]'
        }`}
        title="Live Chart"
      >
        <BarChart3
          className={`w-5 h-5 transition-colors ${
            isActive('/') ? 'text-white' : 'text-[#787B86] group-hover:text-white'
          }`}
        />
        <div className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#0a0e27] border border-[#1e222d] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
          <span className="text-white text-[12px] font-medium">Live Chart</span>
        </div>
      </Link>

      <Link
        to="/chat"
        className={`group relative p-3 rounded-xl transition-all shadow-lg backdrop-blur-sm border ${
          isActive('/chat')
            ? 'bg-gradient-to-br from-purple-500 to-indigo-600 border-purple-500/50 shadow-purple-500/30'
            : 'bg-[#1a1f3a]/80 border-[#1e222d] hover:border-[#8b5cf6]/50 hover:bg-[#1a1f3a]'
        }`}
        title="AI Chat"
      >
        <MessageSquare
          className={`w-5 h-5 transition-colors ${
            isActive('/chat') ? 'text-white' : 'text-[#787B86] group-hover:text-white'
          }`}
        />
        <div className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#0a0e27] border border-[#1e222d] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
          <span className="text-white text-[12px] font-medium">AI Chat</span>
        </div>
      </Link>
    </div>
  );
};
