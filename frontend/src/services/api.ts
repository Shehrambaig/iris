/**
 * API Service - Backend integration
 * Connects frontend to Python backend for real-time data
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface StockData {
  symbol: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  source: string;
  publishedAt: string;
  url: string;
  symbol: string;
  sentiment?: {
    score: number;
    label: string;
    confidence: number;
    summary: string;
  };
  source_type?: 'financial' | 'external';
}

export interface CombinedNewsResponse {
  symbol: string;
  financial_news_count: number;
  external_news_count: number;
  news: NewsArticle[];
}

/**
 * Stock API
 */
export const stockApi = {
  /**
   * Get real-time stock data
   */
  async getStock(symbol: string): Promise<StockData> {
    const response = await fetch(`${API_BASE}/api/stock/${symbol}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch stock ${symbol}`);
    }
    return response.json();
  },

  /**
   * Get multiple stocks at once
   */
  async getMultipleStocks(symbols: string[]): Promise<StockData[]> {
    const response = await fetch(`${API_BASE}/api/stocks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols }),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch stocks');
    }
    return response.json();
  },

  /**
   * Get index data (SPX, NDQ, etc.)
   */
  async getIndex(symbol: string): Promise<StockData> {
    const response = await fetch(`${API_BASE}/api/index/${symbol}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch index ${symbol}`);
    }
    return response.json();
  },

  /**
   * Get historical candlestick data
   */
  async getCandles(
    symbol: string,
    period: string = '6mo',
    interval: string = '1d'
  ): Promise<CandleData[]> {
    const response = await fetch(
      `${API_BASE}/api/candles/${symbol}?period=${period}&interval=${interval}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch candles for ${symbol}`);
    }
    return response.json();
  },
};

/**
 * News API
 */
export const newsApi = {
  /**
   * Get financial news from Yahoo Finance
   */
  async getFinancialNews(symbol: string, limit: number = 10): Promise<NewsArticle[]> {
    const response = await fetch(`${API_BASE}/api/news/${symbol}?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch news for ${symbol}`);
    }
    return response.json();
  },

  /**
   * Search external news using Tavily
   */
  async searchExternalNews(
    symbol: string,
    query: string,
    limit: number = 5
  ): Promise<{ symbol: string; query: string; results: NewsArticle[]; count: number }> {
    const response = await fetch(`${API_BASE}/api/news/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, query, limit }),
    });
    if (!response.ok) {
      throw new Error('Failed to search external news');
    }
    return response.json();
  },

  /**
   * Get combined financial + external news with sentiment
   */
  async getCombinedNews(symbol: string, limit: number = 5): Promise<CombinedNewsResponse> {
    const response = await fetch(`${API_BASE}/api/news/combined/${symbol}?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch combined news for ${symbol}`);
    }
    return response.json();
  },
};

/**
 * Sentiment API
 */
export const sentimentApi = {
  /**
   * Analyze sentiment of text
   */
  async analyze(text: string): Promise<{
    score: number;
    label: string;
    confidence: number;
    summary: string;
  }> {
    const response = await fetch(`${API_BASE}/api/sentiment/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      throw new Error('Failed to analyze sentiment');
    }
    return response.json();
  },
};

/**
 * WebSocket connection for real-time updates
 */
export class StockWebSocket {
  private ws: WebSocket | null = null;
  private symbol: string;
  private onUpdate: (data: any) => void;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(symbol: string, onUpdate: (data: any) => void) {
    this.symbol = symbol;
    this.onUpdate = onUpdate;
  }

  connect() {
    const wsUrl = API_BASE.replace('http', 'ws');
    this.ws = new WebSocket(`${wsUrl}/ws/stock/${this.symbol}`);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for ${this.symbol}`);
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onUpdate(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log(`WebSocket closed for ${this.symbol}`);
      // Auto-reconnect
      this.reconnectTimer = setTimeout(() => {
        console.log(`Reconnecting WebSocket for ${this.symbol}...`);
        this.connect();
      }, this.reconnectInterval);
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  changeSymbol(symbol: string) {
    this.symbol = symbol;
    this.disconnect();
    this.connect();
  }
}
