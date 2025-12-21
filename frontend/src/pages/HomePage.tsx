import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, Sparkles, X, Bell, Newspaper } from 'lucide-react';
import { SymbolIcon } from '../components/SymbolIcon';
import { useNasdaqLiveStocks } from '../hooks/useNasdaqLiveData';
import { useNewsWebSocket } from '../hooks/useNewsWebSocket';
import { analyzePriceSentiment, getSimpleSentimentLabel, type NasdaqStockData } from '../services/priceSentimentService';

interface CompanyData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sentiment: {
    label: string;
    score: number;
    confidence: number;
  };
}

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string;
  company: string;
  publishedAt: string;
  symbol?: string;
  sentiment?: {
    label: string;
    score: number;
  };
}

export const HomePage = () => {
  const navigate = useNavigate();
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [showAllNews, setShowAllNews] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [latestNewsItem, setLatestNewsItem] = useState<NewsItem | null>(null);
  const previousNewsIdRef = useRef<string | null>(null);

  // Fetch live stock data from NASDAQ API (updates every 5 seconds)
  const { stocks: nasdaqStocks, loading: loadingStocks } = useNasdaqLiveStocks();

  // Fetch financial news from scraper
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoadingNews(true);
        console.log('[HomePage] Fetching news from API...');

        const response = await fetch('http://localhost:8000/api/news/all?limit=30');
        const data = await response.json();

        console.log('[HomePage] API response:', data);

        // API returns {count: N, news: [...]}
        if (data && Array.isArray(data.news) && data.news.length > 0) {
          console.log('[HomePage] Setting news:', data.news.length, 'items');

          const latestNewsId = data.news[0].id;

          // Check if there's a new news item (different from previous)
          if (previousNewsIdRef.current && previousNewsIdRef.current !== latestNewsId) {
            // New news detected! Show notification
            console.log('[HomePage] 🔔 NEW NEWS DETECTED!', data.news[0].title);
            setLatestNewsItem(data.news[0]);
            setShowNotification(true);
            // Auto-hide after 5 seconds
            setTimeout(() => setShowNotification(false), 5000);
          }

          // Update the ref with the latest news ID
          previousNewsIdRef.current = latestNewsId;
          setNews(data.news);
        } else {
          console.error('[HomePage] Unexpected API response format:', data);
          setNews([]);
        }
      } catch (error) {
        console.error('[HomePage] Error fetching news:', error);
        setNews([]);
      } finally {
        setLoadingNews(false);
        console.log('[HomePage] Loading complete');
      }
    };

    fetchNews();

    // Refresh news every 30 seconds (fallback if WebSocket fails)
    const interval = setInterval(fetchNews, 30000);
    return () => clearInterval(interval);
  }, []);

  // Real-time news updates via WebSocket (DISABLED in development due to React Strict Mode)
  // Uncomment for production:
  // useNewsWebSocket({
  //   onNewsUpdate: (newNewsItems) => {
  //     console.log('[HomePage] 🔔 WebSocket: Received', newNewsItems.length, 'new articles in real-time!');
  //     setNews((prevNews) => {
  //       const existingIds = new Set(prevNews.map(n => n.id));
  //       const uniqueNewItems = newNewsItems.filter(item => !existingIds.has(item.id));
  //       if (uniqueNewItems.length > 0) {
  //         setLatestNewsItem(uniqueNewItems[0]);
  //         setShowNotification(true);
  //         setTimeout(() => setShowNotification(false), 5000);
  //         return [...uniqueNewItems, ...prevNews].slice(0, 20);
  //       }
  //       return prevNews;
  //     });
  //   },
  //   autoReconnect: true,
  //   reconnectDelay: 3000,
  // });

  // Initialize with mock company data
  const [companies, setCompanies] = useState<CompanyData[]>([
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 193.42,
      change: 2.15,
      changePercent: 1.12,
      sentiment: { label: 'positive', score: 0.78, confidence: 0.92 }
    },
    {
      symbol: 'NVDA',
      name: 'NVIDIA Corporation',
      price: 495.87,
      change: 8.34,
      changePercent: 1.71,
      sentiment: { label: 'positive', score: 0.85, confidence: 0.95 }
    },
    {
      symbol: 'MSFT',
      name: 'Microsoft Corporation',
      price: 378.91,
      change: -1.23,
      changePercent: -0.32,
      sentiment: { label: 'neutral', score: 0.15, confidence: 0.68 }
    },
    {
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      price: 141.56,
      change: 0.87,
      changePercent: 0.62,
      sentiment: { label: 'positive', score: 0.62, confidence: 0.84 }
    },
    {
      symbol: 'AMZN',
      name: 'Amazon.com Inc.',
      price: 178.23,
      change: -2.45,
      changePercent: -1.36,
      sentiment: { label: 'negative', score: -0.45, confidence: 0.76 }
    },
    {
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      price: 248.58,
      change: 5.67,
      changePercent: 2.34,
      sentiment: { label: 'positive', score: 0.71, confidence: 0.88 }
    },
    {
      symbol: 'META',
      name: 'Meta Platforms Inc.',
      price: 489.32,
      change: 3.21,
      changePercent: 0.66,
      sentiment: { label: 'neutral', score: 0.22, confidence: 0.71 }
    },
    {
      symbol: 'AMD',
      name: 'Advanced Micro Devices',
      price: 138.76,
      change: -1.87,
      changePercent: -1.33,
      sentiment: { label: 'negative', score: -0.38, confidence: 0.79 }
    },
    {
      symbol: 'NFLX',
      name: 'Netflix Inc.',
      price: 612.45,
      change: 7.89,
      changePercent: 1.30,
      sentiment: { label: 'positive', score: 0.54, confidence: 0.82 }
    },
    {
      symbol: 'DIS',
      name: 'The Walt Disney Company',
      price: 95.67,
      change: -0.34,
      changePercent: -0.35,
      sentiment: { label: 'neutral', score: -0.12, confidence: 0.65 }
    },
  ]);

  // Update with live NASDAQ data when available - This runs FIRST on initial load
  useEffect(() => {
    if (nasdaqStocks.length > 0) {
      console.log('[HomePage] NASDAQ live data received:', nasdaqStocks.length, 'stocks');
      setCompanies(prevCompanies =>
        prevCompanies.map((company) => {
          // Map GOOGL to GOOG (NASDAQ uses GOOG)
          const symbolToFind = company.symbol === 'GOOGL' ? 'GOOG' : company.symbol;
          const nasdaqStock = nasdaqStocks.find((s) => s.symbol === symbolToFind);
          if (nasdaqStock) {
            // Calculate real sentiment from NASDAQ price data
            const nasdaqData: NasdaqStockData = {
              symbol: nasdaqStock.symbol,
              name: nasdaqStock.name,
              lastSale: `$${nasdaqStock.price.toFixed(2)}`,
              change: nasdaqStock.change >= 0 ? `+${nasdaqStock.change.toFixed(2)}` : nasdaqStock.change.toFixed(2),
              pctChange: `${nasdaqStock.changePercent >= 0 ? '+' : ''}${nasdaqStock.changePercent.toFixed(2)}%`,
              volume: nasdaqStock.volume?.toString() || '0'
            };

            const priceSentiment = analyzePriceSentiment(nasdaqData);
            const simpleSentiment = getSimpleSentimentLabel(priceSentiment);

            console.log(`[HomePage] Updating ${company.symbol} - Price: $${nasdaqStock.price}, Change: ${nasdaqStock.change} (${nasdaqStock.changePercent}%), Sentiment: ${simpleSentiment}`);

            return {
              ...company,
              name: nasdaqStock.name, // Use real name from NASDAQ
              price: nasdaqStock.price,
              change: nasdaqStock.change,
              changePercent: nasdaqStock.changePercent,
              sentiment: {
                label: simpleSentiment,
                score: priceSentiment.score,
                confidence: priceSentiment.confidence
              }
            };
          }
          return company;
        })
      );
    }
  }, [nasdaqStocks]);

  // News notifications are now handled via real API data

  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'positive':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'negative':
        return 'text-red-400 bg-red-500/10 border-red-500/30';
      default:
        return 'text-[#787B86] bg-[#1a1f3a]/50 border-[#1e222d]';
    }
  };

  return (
    <div className="w-screen h-screen bg-gradient-to-b from-[#0a0e27] to-[#0f1420] flex flex-col overflow-hidden">
      {/* Top Bar */}
      <div className="h-14 bg-gradient-to-r from-[#0a0e27] via-[#0d1128] to-[#0a0e27] border-b border-[#1e222d] flex items-center px-6 shadow-lg z-20 relative">
        <div className="flex items-center gap-3">
          {/* Animated Logo */}
          <div className="homepage-logo-container">
            <div className="homepage-logo-line homepage-logo-line-1"></div>
            <div className="homepage-logo-line homepage-logo-line-2"></div>
            <div className="homepage-logo-line homepage-logo-line-3"></div>
            <div className="homepage-logo-line homepage-logo-line-4"></div>
            <div className="homepage-logo-line homepage-logo-line-5"></div>
          </div>
          <div>
            <span className="text-white font-bold text-[16px] leading-tight tracking-tight">MarketPulse</span>
            <p className="text-[#787B86] text-[11px]">Real-time Market Intelligence</p>
          </div>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-4">
          {/* Notifications Button */}
          <button
            onClick={() => setShowAllNews(true)}
            className="relative p-2.5 rounded-xl bg-[#1a1f3a]/40 hover:bg-[#1a1f3a] border border-[#1e222d] hover:border-blue-500/40 text-[#787B86] hover:text-blue-400 transition-all group"
          >
            <Bell className="w-5 h-5" />
            {news.length > 0 && (
              <div className="absolute -top-0.5 -right-0.5 flex items-center justify-center">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg shadow-blue-500/50"></span>
                </span>
              </div>
            )}
          </button>

          {/* AI Chat Button - Premium */}
          <button
            onClick={() => navigate('/chat')}
            className="relative flex items-center gap-2.5 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 rounded-xl border-2 border-purple-400/30 hover:border-purple-300/50 transition-all duration-300 shadow-lg shadow-purple-500/40 hover:shadow-xl hover:shadow-purple-500/60 group overflow-hidden"
            style={{ backdropFilter: 'blur(10px)' }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            <Sparkles className="w-4 h-4 text-white relative z-10 group-hover:rotate-12 transition-transform" />
            <span className="text-white text-[13px] font-bold relative z-10 tracking-wide">AI Chat</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-7xl mx-auto">
          {/* Dashboard Stats - Premium Design */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
            {/* Total Companies */}
            <div className="group relative p-6 bg-gradient-to-br from-[#1a1f3a]/60 via-[#1a1f3a]/40 to-[#1a1f3a]/20 border border-[#1e222d] hover:border-blue-500/40 rounded-2xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/10 overflow-hidden">
              {/* Gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-indigo-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[#787B86] text-[12px] font-semibold uppercase tracking-wider" style={{ marginLeft: '4px', marginTop: '-2px' }}>Companies</span>
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex items-center justify-center shadow-lg shadow-blue-500/20" style={{ transform: 'translate(-4px, 4px)' }}>
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                </div>
                <div className="space-y-1" style={{ marginTop: '-12px', paddingLeft: '16px', paddingRight: '8px' }}>
                  <div className="text-white text-3xl font-bold leading-none">{companies.length}</div>
                  <div className="text-blue-400 text-[11px] font-medium">Actively tracking</div>
                </div>
              </div>
            </div>

            {/* Positive Sentiment */}
            <div className="group relative p-6 bg-gradient-to-br from-[#1a1f3a]/60 via-[#1a1f3a]/40 to-[#1a1f3a]/20 border border-[#1e222d] hover:border-emerald-500/40 rounded-2xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-green-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[#787B86] text-[12px] font-semibold uppercase tracking-wider" style={{ marginLeft: '4px', marginTop: '-2px' }}>Positive</span>
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-600/20 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/20" style={{ transform: 'translate(-4px, 4px)' }}>
                    <TrendingUp className="w-5 h-5 text-emerald-400" />
                  </div>
                </div>
                <div className="space-y-1" style={{ marginTop: '-12px', paddingLeft: '16px', paddingRight: '8px' }}>
                  <div className="text-white text-3xl font-bold leading-none">
                    {companies.filter(c => c.sentiment.label === 'positive').length}
                  </div>
                  <div className="text-emerald-400 text-[11px] font-medium">
                    {Math.round((companies.filter(c => c.sentiment.label === 'positive').length / companies.length) * 100)}% of total
                  </div>
                </div>
              </div>
            </div>

            {/* Negative Sentiment */}
            <div className="group relative p-6 bg-gradient-to-br from-[#1a1f3a]/60 via-[#1a1f3a]/40 to-[#1a1f3a]/20 border border-[#1e222d] hover:border-red-500/40 rounded-2xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl hover:shadow-red-500/10 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-rose-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[#787B86] text-[12px] font-semibold uppercase tracking-wider" style={{ marginLeft: '4px', marginTop: '-2px' }}>Negative</span>
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-500/20 to-rose-600/20 border border-red-500/30 flex items-center justify-center shadow-lg shadow-red-500/20" style={{ transform: 'translate(-4px, 4px)' }}>
                    <TrendingDown className="w-5 h-5 text-red-400" />
                  </div>
                </div>
                <div className="space-y-1" style={{ marginTop: '-12px', paddingLeft: '16px', paddingRight: '8px' }}>
                  <div className="text-white text-3xl font-bold leading-none">
                    {companies.filter(c => c.sentiment.label === 'negative').length}
                  </div>
                  <div className="text-red-400 text-[11px] font-medium">
                    {Math.round((companies.filter(c => c.sentiment.label === 'negative').length / companies.length) * 100)}% of total
                  </div>
                </div>
              </div>
            </div>

            {/* Average Confidence */}
            <div className="group relative p-6 bg-gradient-to-br from-[#1a1f3a]/60 via-[#1a1f3a]/40 to-[#1a1f3a]/20 border border-[#1e222d] hover:border-purple-500/40 rounded-2xl backdrop-blur-sm transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/10 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[#787B86] text-[12px] font-semibold uppercase tracking-wider" style={{ marginLeft: '4px', marginTop: '-2px' }}>Confidence</span>
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-600/20 border border-purple-500/30 flex items-center justify-center shadow-lg shadow-purple-500/20" style={{ transform: 'translate(-4px, 4px)' }}>
                    <Sparkles className="w-5 h-5 text-purple-400" />
                  </div>
                </div>
                <div className="space-y-1" style={{ marginTop: '-12px', paddingLeft: '16px', paddingRight: '8px' }}>
                  <div className="text-white text-3xl font-bold leading-none">
                    {Math.round((companies.reduce((acc, c) => acc + c.sentiment.confidence, 0) / companies.length) * 100)}%
                  </div>
                  <div className="text-purple-400 text-[11px] font-medium">AI analysis accuracy</div>
                </div>
              </div>
            </div>
          </div>

          {/* Companies Section Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-white text-2xl font-bold mb-1">Companies</h2>
              <p className="text-[#787B86] text-sm">Click on any company to view detailed analysis</p>
            </div>
          </div>

          {/* Companies List - Smooth Professional Layout */}
          <div className="space-y-4 max-w-6xl mx-auto">
            {companies.map((company) => (
              <div
                key={company.symbol}
                onClick={() => navigate(`/graph/${company.symbol}`)}
                className="group relative p-6 bg-gradient-to-r from-[#1a1f3a]/40 via-[#1a1f3a]/30 to-[#1a1f3a]/20 border border-[#1e222d] hover:border-[#2962FF]/50 rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/10 backdrop-blur-sm hover:translate-x-2"
              >
                <div className="flex items-center gap-6">
                  {/* Company Icon */}
                  <div className="relative flex-shrink-0">
                    <div className="w-16 h-16 rounded-xl bg-[#0a0e27]/50 border border-[#1e222d] flex items-center justify-center group-hover:border-[#2962FF]/40 transition-all">
                      <SymbolIcon symbol={company.symbol} size={40} />
                    </div>
                    {/* Glow effect */}
                    <div className="absolute inset-0 bg-blue-400/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>

                  {/* Company Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-3 mb-1">
                      <h3 className="text-white font-bold text-xl">{company.symbol}</h3>
                      <span className="text-[#787B86] text-sm">{company.name}</span>
                    </div>
                    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[12px] font-semibold ${getSentimentColor(company.sentiment.label)}`}>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span className="capitalize">{company.sentiment.label}</span>
                      <span className="opacity-70">•</span>
                      <span className="opacity-80">{Math.round(company.sentiment.confidence * 100)}%</span>
                    </div>
                  </div>

                  {/* Price Info */}
                  <div className="flex-shrink-0 text-right">
                    <div className="text-white text-2xl font-bold mb-1">${company.price.toFixed(2)}</div>
                    <div className={`flex items-center justify-end gap-1.5 text-[13px] font-semibold ${company.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                      {company.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      <span>
                        {company.change >= 0 ? '+' : ''}{company.change.toFixed(2)} ({company.changePercent >= 0 ? '+' : ''}{company.changePercent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>


      {/* All News Modal */}
      {showAllNews && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-4xl max-h-[80vh] m-6 bg-gradient-to-br from-[#1a1f3a]/98 to-[#0a0e27]/98 border border-[#2962FF]/40 rounded-2xl shadow-2xl shadow-blue-500/30 overflow-hidden">
            {/* Gradient glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />

            {/* Header */}
            <div className="relative px-8 py-6 border-b border-[#1e222d] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/30 flex items-center justify-center shadow-lg">
                  <Newspaper className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-white text-2xl font-bold">Financial Market News</h2>
                  <p className="text-[#787B86] text-sm">{news.length} total articles</p>
                </div>
              </div>
              <button
                onClick={() => setShowAllNews(false)}
                className="w-10 h-10 rounded-xl hover:bg-[#1a1f3a] transition-all flex items-center justify-center group"
              >
                <X className="w-5 h-5 text-[#787B86] group-hover:text-white transition-colors" />
              </button>
            </div>

            {/* News List */}
            <div className="relative overflow-y-auto max-h-[calc(80vh-140px)] p-6">
              {loadingNews ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-white text-lg">Loading news...</p>
                </div>
              ) : news.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-white text-lg">No news available</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {news.map((item, index) => (
                    <div
                      key={item.id}
                      style={{
                        background: '#1e3a8a',
                        border: '2px solid #3b82f6',
                        padding: '16px',
                        borderRadius: '8px',
                        marginBottom: '12px',
                        cursor: 'pointer'
                      }}
                      onClick={() => window.open(item.url, '_blank')}
                    >
                      <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
                        {item.company} - {item.title}
                      </h3>
                      <p style={{ color: '#9ca3af', fontSize: '14px' }}>
                        {item.source} • {new Date(item.publishedAt).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* News Notification Popup */}
      {showNotification && latestNewsItem && (
        <div
          style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: 9999,
            background: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)',
            border: '2px solid #60a5fa',
            borderRadius: '12px',
            padding: '20px',
            minWidth: '350px',
            maxWidth: '450px',
            boxShadow: '0 10px 40px rgba(59, 130, 246, 0.5)',
            animation: 'slideInRight 0.5s ease-out'
          }}
          onClick={() => {
            window.open(latestNewsItem.url, '_blank');
            setShowNotification(false);
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer' }}>
            <div style={{
              background: '#3b82f6',
              borderRadius: '8px',
              padding: '8px',
              flexShrink: 0
            }}>
              <Newspaper style={{ width: '24px', height: '24px', color: '#ffffff' }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{
                color: '#60a5fa',
                fontSize: '12px',
                fontWeight: 'bold',
                marginBottom: '4px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                Breaking News • {latestNewsItem.company}
              </div>
              <h4 style={{
                color: '#ffffff',
                fontSize: '16px',
                fontWeight: 'bold',
                marginBottom: '8px',
                lineHeight: '1.4'
              }}>
                {latestNewsItem.title}
              </h4>
              <p style={{ color: '#93c5fd', fontSize: '13px' }}>
                {latestNewsItem.source} • Just now
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowNotification(false);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#93c5fd',
                cursor: 'pointer',
                fontSize: '20px',
                padding: '4px',
                flexShrink: 0
              }}
            >
              ×
            </button>
          </div>
        </div>
      )}

      <style>{`
        /* News Notification Animation */
        @keyframes slideInRight {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        /* Premium Animated Logo */
        .homepage-logo-container {
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

        .homepage-logo-container::before {
          content: '';
          position: absolute;
          inset: -10px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent 60%);
          border-radius: 20px;
          filter: blur(15px);
          animation: pulse-homepage-logo 3s ease-in-out infinite;
          z-index: -1;
        }

        .homepage-logo-line {
          width: 2px;
          border-radius: 1px;
          position: relative;
          animation: homepage-logo-bounce 2s ease-in-out infinite;
        }

        .homepage-logo-line-1 {
          height: 10px;
          background: linear-gradient(180deg, rgba(59, 130, 246, 0.9), rgba(59, 130, 246, 1));
          filter: drop-shadow(0 0 3px rgba(59, 130, 246, 0.8));
          animation-delay: 0s;
        }

        .homepage-logo-line-2 {
          height: 16px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.15s;
        }

        .homepage-logo-line-3 {
          height: 22px;
          background: linear-gradient(180deg, rgba(99, 102, 241, 0.9), rgba(99, 102, 241, 1));
          filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.9));
          animation-delay: 0.3s;
        }

        .homepage-logo-line-4 {
          height: 14px;
          background: linear-gradient(180deg, rgba(139, 92, 246, 0.9), rgba(139, 92, 246, 1));
          filter: drop-shadow(0 0 3px rgba(139, 92, 246, 0.8));
          animation-delay: 0.45s;
        }

        .homepage-logo-line-5 {
          height: 18px;
          background: linear-gradient(180deg, rgba(16, 185, 129, 0.9), rgba(16, 185, 129, 1));
          filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.8));
          animation-delay: 0.6s;
        }

        @keyframes homepage-logo-bounce {
          0%, 100% {
            transform: scaleY(1) translateY(0);
            opacity: 0.85;
          }
          50% {
            transform: scaleY(1.2) translateY(-2px);
            opacity: 1;
          }
        }

        @keyframes pulse-homepage-logo {
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
