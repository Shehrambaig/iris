import { useEffect, useState } from 'react';
import { Newspaper, ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';
import { API_BASE } from '../services/api';

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string;
  company: string;
  publishedAt: string;
  sentiment?: {
    label: string;
    score: number;
  };
}

interface NewsFeedProps {
  maxItems?: number;
  className?: string;
}

export const NewsFeed = ({ maxItems = 10, className = '' }: NewsFeedProps) => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch news without sentiment for faster response
      const response = await fetch(`${API_BASE}/api/news/all?limit_per_company=3&skip_sentiment=true`);
      const data = await response.json();

      if (data && data.news) {
        setNews(data.news.slice(0, maxItems));
      }
    } catch (err) {
      setError('Failed to load news');
      console.error('Error fetching news:', err);
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

      if (diffHours < 1) {
        return 'Just now';
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else if (diffDays < 7) {
        return `${diffDays}d ago`;
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }
    } catch {
      return 'Recent';
    }
  };

  const getSentimentIcon = (sentiment?: { label: string; score: number }) => {
    if (!sentiment) return null;

    if (sentiment.label === 'positive') {
      return <TrendingUp className="w-3 h-3 text-green-400" />;
    } else if (sentiment.label === 'negative') {
      return <TrendingDown className="w-3 h-3 text-red-400" />;
    }
    return null;
  };

  if (loading) {
    return (
      <div className={`bg-[#1a1a1a] rounded-lg p-4 border border-zinc-800 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Market News</h3>
        </div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-zinc-800 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-zinc-800 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-[#1a1a1a] rounded-lg p-4 border border-zinc-800 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Market News</h3>
        </div>
        <p className="text-zinc-400 text-sm">{error}</p>
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className={`bg-[#1a1a1a] rounded-lg p-4 border border-zinc-800 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Market News</h3>
        </div>
        <p className="text-zinc-400 text-sm">No news available</p>
      </div>
    );
  }

  return (
    <div className={`bg-[#1a1a1a] rounded-lg p-4 border border-zinc-800 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Market News</h3>
        </div>
        <button
          onClick={fetchNews}
          className="text-xs text-zinc-400 hover:text-white transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
        {news.map((item) => (
          <a
            key={item.id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 bg-zinc-900/50 rounded-lg border border-zinc-800/50 hover:border-blue-500/30 hover:bg-zinc-900/80 transition-all group"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors line-clamp-2 flex-1">
                {item.title}
              </h4>
              <ExternalLink className="w-3 h-3 text-zinc-500 group-hover:text-blue-400 flex-shrink-0 mt-0.5" />
            </div>

            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <span className="font-medium text-zinc-300">{item.company}</span>
              <span>•</span>
              <span>{formatDate(item.publishedAt)}</span>
              {item.sentiment && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    {getSentimentIcon(item.sentiment)}
                    <span className="capitalize">{item.sentiment.label}</span>
                  </div>
                </>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};
