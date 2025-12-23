import { useState, useEffect } from 'react';
import type { StockData, IndexData } from '../types';
import { SymbolIcon } from './SymbolIcon';
import { API_BASE } from '../services/api';
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Star,
  ExternalLink,
  Newspaper
} from 'lucide-react';

interface RightSidebarProps {
  indices: IndexData[];
  stocks: StockData[];
  selectedStock: StockData;
  onStockSelect?: (symbol: string) => void;
}

interface ContextualNews {
  id: string;
  title: string;
  url: string;
  content: string;
  source: string;
  publishedAt: string;
  type: 'contextual';
  sentiment?: {
    label: string;
    score: number;
  };
}

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string;
  company: string;
  publishedAt: string;
  type: 'financial';
  sentiment?: {
    label: string;
    score: number;
  };
  contextual_news?: ContextualNews[];
  has_context?: boolean;
}

export const RightSidebar = ({ indices, stocks, selectedStock, onStockSelect }: RightSidebarProps) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);

  // Fetch news when selected stock changes
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoadingNews(true);
        // Disable context and sentiment for faster response
        const response = await fetch(`${API_BASE}/api/news/${selectedStock.symbol}?limit=2&include_context=false&skip_sentiment=true`);
        const data = await response.json();

        if (Array.isArray(data)) {
          setNews(data.slice(0, 2));
        }
      } catch (error) {
        console.error('Error fetching news:', error);
      } finally {
        setLoadingNews(false);
      }
    };

    fetchNews();
  }, [selectedStock.symbol]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recent';
    }
  };

  return (
    <div className="flex h-full bg-gradient-to-b from-[#0a0e27] to-[#0f1420] border-l border-[#1e222d]">
      <div className="w-80 flex flex-col h-full">
        {/* Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-[#1e222d] shrink-0">
          <span className="text-[13px] font-bold text-white">Market Watch</span>
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-500/50" />
            <span className="text-emerald-400 text-[11px] font-bold uppercase tracking-wider">Live</span>
          </div>
        </div>

        {/* List Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
          {/* Indices Section */}
          <div>
            <div className="flex items-center gap-2 mb-3 px-2">
              <TrendingUp className="w-4 h-4 text-[#787B86]" />
              <span className="text-[11px] font-bold text-[#787B86] uppercase tracking-wider">Market Indices</span>
            </div>
            <div className="space-y-2">
              {indices.map((index) => (
                <ModernWatchlistItem key={index.symbol} data={index} />
              ))}
            </div>
          </div>

          {/* Stocks Section */}
          <div className="pt-2">
            <div className="flex items-center gap-2 mb-3 px-2">
              <Star className="w-4 h-4 text-[#787B86]" />
              <span className="text-[11px] font-bold text-[#787B86] uppercase tracking-wider">Top Stocks</span>
            </div>
            <div className="space-y-2">
              {stocks.map((stock) => (
                <ModernWatchlistItem
                  key={stock.symbol}
                  data={stock}
                  isSelected={selectedStock.symbol === stock.symbol}
                  onClick={() => onStockSelect?.(stock.symbol)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Selected Stock Details (Bottom Panel) */}
        <div className="border-t border-[#1e222d] shrink-0 bg-gradient-to-b from-[#0d1128] to-[#0a0e27]">
          <div className="p-4 border-b border-[#1e222d]">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex items-center justify-center shadow-lg">
                  <SymbolIcon symbol={selectedStock.symbol} size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[16px] font-bold text-white">{selectedStock.symbol}</span>
                    {selectedStock.change >= 0 ? (
                      <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <ArrowDownRight className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                  <span className="text-[11px] text-[#787B86]">{selectedStock.name}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-white">${selectedStock.price.toFixed(2)}</span>
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${
                  selectedStock.change >= 0
                    ? 'bg-emerald-500/15 border-emerald-500/30'
                    : 'bg-red-500/15 border-red-500/30'
                }`}>
                  <span className={`text-sm font-bold ${
                    selectedStock.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {selectedStock.change >= 0 ? '+' : ''}{selectedStock.change.toFixed(2)} ({selectedStock.changePercent >= 0 ? '+' : ''}{selectedStock.changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-[#787B86] flex items-center gap-2">
                <span>Electronic Technology • Semiconductors</span>
              </div>
            </div>
          </div>

          <div className="p-3 space-y-3">
            {loadingNews ? (
              <div className="p-3 bg-[#1a1f3a]/50 border border-[#1e222d] rounded-lg">
                <div className="animate-pulse space-y-2">
                  <div className="h-3 bg-zinc-800 rounded w-full"></div>
                  <div className="h-3 bg-zinc-800 rounded w-3/4"></div>
                </div>
              </div>
            ) : news.length === 0 ? (
              <div className="p-3 bg-[#1a1f3a]/50 border border-[#1e222d] rounded-lg">
                <div className="flex justify-between items-start gap-2">
                  <p className="text-[11px] text-[#b4b8c2] leading-relaxed line-clamp-3">
                    No recent news available for {selectedStock.symbol}.
                  </p>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-[10px] text-[#787B86]">MarketPulse</span>
                  <span className="text-[10px] text-[#787B86]">Just now</span>
                </div>
              </div>
            ) : (
              <>
                {news.slice(0, 1).map((item) => (
                  <a
                    key={item.id}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-[#1a1f3a]/50 border border-[#1e222d] rounded-lg hover:border-[#2962FF]/30 transition-colors cursor-pointer"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <p className="text-[11px] text-[#b4b8c2] leading-relaxed line-clamp-3">
                        {item.title}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[#787B86]">{item.source || item.company}</span>
                        {item.sentiment && (
                          <>
                            <span className="text-[10px] text-[#787B86]">•</span>
                            <span className={`text-[10px] font-medium capitalize ${
                              item.sentiment.label === 'positive' ? 'text-emerald-400' :
                              item.sentiment.label === 'negative' ? 'text-red-400' :
                              'text-[#787B86]'
                            }`}>
                              {item.sentiment.label}
                            </span>
                          </>
                        )}
                      </div>
                      <span className="text-[10px] text-[#787B86]">{formatDate(item.publishedAt)}</span>
                    </div>
                  </a>
                ))}

                {/* Contextual news as additional items */}
                {news[0]?.contextual_news && news[0].contextual_news.slice(0, 1).map((contextItem) => (
                  <a
                    key={contextItem.id}
                    href={contextItem.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-[#1a1f3a]/50 border border-[#1e222d] rounded-lg hover:border-[#2962FF]/30 transition-colors cursor-pointer"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <p className="text-[11px] text-[#b4b8c2] leading-relaxed line-clamp-3">
                        {contextItem.title}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[#787B86]">{contextItem.source}</span>
                        {contextItem.sentiment && (
                          <>
                            <span className="text-[10px] text-[#787B86]">•</span>
                            <span className={`text-[10px] font-medium capitalize ${
                              contextItem.sentiment.label === 'positive' ? 'text-emerald-400' :
                              contextItem.sentiment.label === 'negative' ? 'text-red-400' :
                              'text-[#787B86]'
                            }`}>
                              {contextItem.sentiment.label}
                            </span>
                          </>
                        )}
                      </div>
                      <span className="text-[10px] text-[#787B86]">Recent</span>
                    </div>
                  </a>
                ))}
              </>
            )}

            <div className="pt-2 border-t border-[#1e222d]/50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[11px] text-[#787B86] font-medium">Key Stats</span>
                <span className="text-[11px] text-[#2962FF] cursor-pointer hover:underline font-medium">More</span>
              </div>
              <div className="grid grid-cols-2 gap-y-2 gap-x-4">
                <div className="flex justify-between">
                  <span className="text-[11px] text-[#787B86]">Volume</span>
                  <span className="text-[11px] text-white font-medium">
                    {selectedStock.volume
                      ? typeof selectedStock.volume === 'string'
                        ? (parseFloat(selectedStock.volume.replace(/,/g, '')) / 1000000).toFixed(2) + 'M'
                        : (selectedStock.volume / 1000000).toFixed(2) + 'M'
                      : '111.36M'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[11px] text-[#787B86]">Avg Vol</span>
                  <span className="text-[11px] text-white font-medium">425.1M</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[11px] text-[#787B86]">Mkt Cap</span>
                  <span className="text-[11px] text-white font-medium">3.12T</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[11px] text-[#787B86]">PE Ratio</span>
                  <span className="text-[11px] text-white font-medium">72.4</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ModernWatchlistItem = ({ data, isSelected, onClick }: { data: IndexData | StockData, isSelected?: boolean, onClick?: () => void }) => {
  const isPositive = data.change >= 0;

  return (
    <div
      onClick={onClick}
      className={`group relative p-3 rounded-lg cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'bg-gradient-to-br from-blue-500/15 to-indigo-600/10 border-2 border-[#2962FF]/50 shadow-lg shadow-blue-500/10'
          : 'bg-[#1a1f3a]/40 border border-[#1e222d] hover:border-[#2962FF]/30 hover:bg-[#1a1f3a]/60'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            isSelected
              ? 'bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/40 shadow-lg'
              : 'bg-[#0d1128] border border-[#1e222d] group-hover:border-[#2962FF]/30'
          }`}>
            <SymbolIcon symbol={data.symbol} size={20} />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[13px] font-bold text-white truncate">{data.symbol}</span>
            <span className="text-[10px] text-[#787B86] truncate">{data.name}</span>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[14px] font-bold text-white mb-1">
            ${data.price.toFixed(2)}
          </span>
          <div className={`flex items-center gap-1 px-2 py-1 rounded-md border ${
            isPositive
              ? 'bg-emerald-500/15 border-emerald-500/30'
              : 'bg-red-500/15 border-red-500/30'
          }`}>
            {isPositive ? (
              <TrendingUp className="w-3 h-3 text-emerald-400" />
            ) : (
              <TrendingDown className="w-3 h-3 text-red-400" />
            )}
            <span className={`text-[11px] font-bold ${
              isPositive ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {isPositive ? '+' : ''}{data.changePercent.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

    </div>
  );
};
