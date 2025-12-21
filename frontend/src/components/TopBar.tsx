import React, { useState, useMemo } from 'react';
import { TrendingUp, TrendingDown, BarChart3, Search, MessageSquare, Home } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { IndexData, StockData } from '../types';
import { analyzePriceSentiment, getSentimentColor, getSentimentEmoji, type NasdaqStockData } from '../services/priceSentimentService';

interface TopBarProps {
  symbol: string;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
  selectedStock?: StockData;
  indices?: IndexData[];
}

export const TopBar: React.FC<TopBarProps> = ({
  symbol,
  timeframe,
  onTimeframeChange,
  selectedStock,
  indices = []
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // Get market status (simplified - assuming open during business hours EST)
  const now = new Date();
  const hours = now.getUTCHours();
  const isMarketOpen = hours >= 14 && hours < 21; // 9:30 AM - 4 PM EST

  // Calculate price-based sentiment
  const priceSentiment = useMemo(() => {
    if (!selectedStock) return null;

    const nasdaqData: NasdaqStockData = {
      symbol: symbol,
      name: selectedStock.name || symbol,
      lastSale: `$${selectedStock.price.toFixed(2)}`,
      change: selectedStock.change >= 0 ? `+${selectedStock.change.toFixed(2)}` : selectedStock.change.toFixed(2),
      pctChange: `${selectedStock.changePercent >= 0 ? '+' : ''}${selectedStock.changePercent.toFixed(2)}%`,
      volume: '0' // We don't have volume in StockData, but it's not critical for display
    };

    return analyzePriceSentiment(nasdaqData);
  }, [selectedStock, symbol]);

  return (
    <div className="h-14 bg-gradient-to-r from-[#0a0e27] via-[#0d1128] to-[#0a0e27] border-b border-[#1e222d] flex items-center px-6 select-none shadow-lg">
      {/* Left: Branding + Symbol */}
      <div className="flex items-center gap-6">
        {/* Branding */}
        <div className="flex items-center gap-3">
          <div className="topbar-logo-container">
            <div className="topbar-logo-line topbar-logo-line-1"></div>
            <div className="topbar-logo-line topbar-logo-line-2"></div>
            <div className="topbar-logo-line topbar-logo-line-3"></div>
            <div className="topbar-logo-line topbar-logo-line-4"></div>
            <div className="topbar-logo-line topbar-logo-line-5"></div>
          </div>
          <div className="flex flex-col">
            <span className="text-white font-bold text-[16px] leading-tight tracking-tight">MarketPulse</span>
          </div>
        </div>

        <div className="w-[1px] h-8 bg-[#1e222d]" />

        {/* Current Symbol */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-white font-bold text-[16px]">{symbol}</span>
              <span className="text-[#787B86] text-[11px] px-2 py-0.5 bg-[#1a1f3a] rounded">NASDAQ</span>
            </div>
            {selectedStock && (
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-white text-[13px] font-semibold">${selectedStock.price.toFixed(2)}</span>
                <div className={`flex items-center gap-1 text-[11px] font-medium ${
                  selectedStock.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {selectedStock.change >= 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  <span>
                    {selectedStock.change >= 0 ? '+' : ''}{selectedStock.change.toFixed(2)}
                    ({selectedStock.changePercent >= 0 ? '+' : ''}{selectedStock.changePercent.toFixed(2)}%)
                  </span>
                </div>
                {priceSentiment && (
                  <div
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded-md border transition-all"
                    style={{
                      borderColor: getSentimentColor(priceSentiment) + '40',
                      backgroundColor: getSentimentColor(priceSentiment) + '15',
                    }}
                    title={priceSentiment.summary}
                  >
                    <span className="text-[10px]">{getSentimentEmoji(priceSentiment)}</span>
                    <span
                      className="text-[10px] font-bold capitalize"
                      style={{ color: getSentimentColor(priceSentiment) }}
                    >
                      {priceSentiment.label.replace('_', ' ')}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Center: Search Bar */}
      <div className="flex-1 flex justify-center items-center px-8">
        <div className="relative w-full max-w-md flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-[#787B86] pointer-events-none z-10" />
          <input
            type="text"
            placeholder="Search stocks, indices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-9 pl-10 pr-4 bg-[#1a1f3a]/50 border border-[#1e222d] rounded-lg text-[13px] text-white placeholder-[#787B86] focus:outline-none focus:border-[#2962FF]/50 focus:bg-[#1a1f3a] transition-all"
          />
        </div>
      </div>

      {/* Right: Timeframes + Status */}
      <div className="flex items-center gap-4">
        {/* Timeframes */}
        <div className="flex items-center gap-1 bg-[#1a1f3a]/30 rounded-lg p-1">
          {['1D', '5D', '1M', '3M', '6M', '1Y', 'All'].map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange(tf)}
              className={`px-3 py-1.5 text-[12px] font-medium rounded-md transition-all ${
                timeframe === tf
                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg'
                  : 'text-[#787B86] hover:text-white hover:bg-[#1a1f3a]'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        <div className="w-[1px] h-8 bg-[#1e222d]" />

        {/* Navigation Buttons */}
        <button
          onClick={() => navigate('/')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all ${
            location.pathname === '/'
              ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
              : 'bg-[#1a1f3a] border-[#1e222d] text-[#787B86] hover:text-white hover:border-[#2962FF]/30'
          }`}
          title="Home"
        >
          <Home className="w-4 h-4" />
          <span className="text-[12px] font-medium">Home</span>
        </button>

        <button
          onClick={() => navigate('/chat')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all ${
            location.pathname === '/chat'
              ? 'bg-purple-500/20 border-purple-500/40 text-purple-400'
              : 'bg-[#1a1f3a] border-[#1e222d] text-[#787B86] hover:text-white hover:border-[#8b5cf6]/30'
          }`}
          title="AI Chat"
        >
          <MessageSquare className="w-4 h-4" />
          <span className="text-[12px] font-medium">AI Chat</span>
        </button>

        <div className="w-[1px] h-8 bg-[#1e222d]" />

        {/* Market Status */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${
          isMarketOpen
            ? 'bg-emerald-500/10 border-emerald-500/30'
            : 'bg-[#1a1f3a] border-[#1e222d]'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            isMarketOpen ? 'bg-emerald-400' : 'bg-[#787B86]'
          }`} />
          <span className={`text-[11px] font-medium ${
            isMarketOpen ? 'text-emerald-400' : 'text-[#787B86]'
          }`}>
            {isMarketOpen ? 'Market Open' : 'Market Closed'}
          </span>
        </div>

        {/* Live Data Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-500/50" />
          <span className="text-emerald-400 text-[11px] font-bold uppercase tracking-wider">Live</span>
        </div>
      </div>

      <style>{`
        /* Premium Animated Logo */
        .topbar-logo-container {
          display: flex;
          align-items: flex-end;
          justify-content: center;
          gap: 4px;
          height: 36px;
          width: 36px;
          padding: 4px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.15), transparent 70%);
          border-radius: 10px;
          position: relative;
        }

        .topbar-logo-container::before {
          content: '';
          position: absolute;
          inset: -10px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent 60%);
          border-radius: 20px;
          filter: blur(15px);
          animation: pulse-topbar-logo 3s ease-in-out infinite;
          z-index: -1;
        }

        .topbar-logo-line {
          width: 2px;
          border-radius: 1px;
          position: relative;
          animation: topbar-logo-bounce 2s ease-in-out infinite;
        }

        .topbar-logo-line-1 {
          height: 10px;
          background: linear-gradient(180deg, rgba(59, 130, 246, 0.9), rgba(59, 130, 246, 1));
          filter: drop-shadow(0 0 3px rgba(59, 130, 246, 0.8));
          animation-delay: 0s;
        }

        .topbar-logo-line-2 {
          height: 16px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.15s;
        }

        .topbar-logo-line-3 {
          height: 22px;
          background: linear-gradient(180deg, rgba(99, 102, 241, 0.9), rgba(99, 102, 241, 1));
          filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.9));
          animation-delay: 0.3s;
        }

        .topbar-logo-line-4 {
          height: 14px;
          background: linear-gradient(180deg, rgba(139, 92, 246, 0.9), rgba(139, 92, 246, 1));
          filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.8));
          animation-delay: 0.45s;
        }

        .topbar-logo-line-5 {
          height: 18px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.6s;
        }

        @keyframes topbar-logo-bounce {
          0%, 100% {
            transform: scaleY(1) translateY(0);
            opacity: 0.85;
          }
          50% {
            transform: scaleY(1.2) translateY(-2px);
            opacity: 1;
          }
        }

        @keyframes pulse-topbar-logo {
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
