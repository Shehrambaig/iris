import { useState, useEffect } from 'react';
import { Newspaper, ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';

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

interface CompactNewsProps {
  symbol: string;
  className?: string;
}

export const CompactNews = ({ symbol, className = '' }: CompactNewsProps) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNews();
  }, [symbol]);

  const fetchNews = async () => {
    try {
      setLoading(true);
      // Fetch combined news (financial + contextual) with sentiment for specific symbol
      const response = await fetch(`http://localhost:8000/api/news/${symbol}?limit=2&include_context=true`);
      const data = await response.json();

      if (Array.isArray(data)) {
        setNews(data.slice(0, 2)); // Show max 2 financial news items
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);

      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recent';
    }
  };

  const getSentimentIcon = (sentiment?: { label: string; score: number }) => {
    if (!sentiment) return null;
    if (sentiment.label === 'positive') {
      return <TrendingUp className="w-3 h-3 text-emerald-400" />;
    } else if (sentiment.label === 'negative') {
      return <TrendingDown className="w-3 h-3 text-red-400" />;
    }
    return null;
  };

  if (loading) {
    return (
      <div className={`bg-gradient-to-br from-[#0a0e27]/95 via-[#0d1128]/95 to-[#0a0e27]/95 backdrop-blur-xl border border-[#1e222d] rounded-xl p-3 shadow-2xl ${className}`}>
        <div className="flex items-center gap-2 mb-2">
          <Newspaper className="w-4 h-4 text-blue-400" />
          <h3 className="text-white text-xs font-semibold">Latest News</h3>
        </div>
        <div className="space-y-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-3 bg-zinc-800 rounded w-full mb-1"></div>
              <div className="h-2 bg-zinc-800 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (news.length === 0) {
    return null; // Don't show if no news
  }

  return (
    <div className={`bg-gradient-to-br from-[#0a0e27]/95 via-[#0d1128]/95 to-[#0a0e27]/95 backdrop-blur-xl border border-[#1e222d] rounded-xl p-3 shadow-2xl ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-blue-400" />
          <h3 className="text-white text-xs font-semibold">Latest News</h3>
        </div>
        <button
          onClick={fetchNews}
          className="text-[10px] text-zinc-400 hover:text-white transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3">
        {news.map((item) => (
          <div key={item.id} className="space-y-1.5">
            {/* Financial News */}
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 hover:border-blue-500/50 rounded-lg transition-all group"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className="text-white text-[11px] font-medium group-hover:text-blue-400 transition-colors line-clamp-2 flex-1 leading-tight">
                  {item.title}
                </h4>
                <ExternalLink className="w-3 h-3 text-blue-400 group-hover:text-blue-300 flex-shrink-0 mt-0.5" />
              </div>

              <div className="flex items-center gap-1.5 text-[10px]">
                <span className="text-blue-400 font-semibold">Financial</span>
                <span className="text-zinc-500">•</span>
                <span className="text-zinc-400">{formatDate(item.publishedAt)}</span>
                {item.sentiment && (
                  <>
                    <span className="text-zinc-500">•</span>
                    <div className="flex items-center gap-1">
                      {getSentimentIcon(item.sentiment)}
                      <span className={`capitalize ${
                        item.sentiment.label === 'positive' ? 'text-emerald-400' :
                        item.sentiment.label === 'negative' ? 'text-red-400' :
                        'text-zinc-400'
                      }`}>{item.sentiment.label}</span>
                    </div>
                  </>
                )}
              </div>
            </a>

            {/* Contextual News from Tavily */}
            {item.contextual_news && item.contextual_news.length > 0 && (
              <div className="ml-3 space-y-1">
                {item.contextual_news.map((contextItem) => (
                  <a
                    key={contextItem.id}
                    href={contextItem.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-1.5 bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/20 hover:border-purple-500/40 rounded transition-all group"
                  >
                    <div className="flex items-start justify-between gap-1.5 mb-0.5">
                      <h5 className="text-zinc-300 text-[10px] font-normal group-hover:text-purple-300 transition-colors line-clamp-1 flex-1 leading-tight">
                        {contextItem.title}
                      </h5>
                      <ExternalLink className="w-2.5 h-2.5 text-purple-400 opacity-60 group-hover:opacity-100 flex-shrink-0 mt-0.5" />
                    </div>

                    <div className="flex items-center gap-1 text-[9px]">
                      <span className="text-purple-400 font-semibold">Context</span>
                      <span className="text-zinc-600">•</span>
                      <span className="text-zinc-500">{contextItem.source}</span>
                      {contextItem.sentiment && (
                        <>
                          <span className="text-zinc-600">•</span>
                          <span className={`capitalize ${
                            contextItem.sentiment.label === 'positive' ? 'text-emerald-400' :
                            contextItem.sentiment.label === 'negative' ? 'text-red-400' :
                            'text-zinc-500'
                          }`}>{contextItem.sentiment.label}</span>
                        </>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
