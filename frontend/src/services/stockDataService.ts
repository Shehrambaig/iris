// Stock Data Service - Fetches real-time data from APIs
// This service can be configured to use yfinance (via backend) or Nasdaq API

export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
  timestamp: number;
}

export interface IndexQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Fetch stock data from backend (which uses yfinance or Nasdaq API)
export const fetchStockData = async (symbol: string): Promise<StockQuote | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stock/${symbol}`);
    if (!response.ok) throw new Error('Failed to fetch stock data');
    const data = await response.json();
    return {
      symbol: data.symbol || symbol,
      price: data.price || data.currentPrice || 0,
      change: data.change || 0,
      changePercent: data.changePercent || 0,
      volume: data.volume || 0,
      high: data.high || data.price || 0,
      low: data.low || data.price || 0,
      open: data.open || data.price || 0,
      close: data.close || data.price || 0,
      timestamp: Date.now(),
    };
  } catch (error) {
    console.error(`Error fetching stock data for ${symbol}:`, error);
    return null;
  }
};

// Fetch multiple stocks at once
export const fetchMultipleStocks = async (symbols: string[]): Promise<StockQuote[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stocks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols }),
    });
    if (!response.ok) throw new Error('Failed to fetch stocks data');
    const data = await response.json();
    return data.map((stock: any) => ({
      symbol: stock.symbol,
      price: stock.price || stock.currentPrice || 0,
      change: stock.change || 0,
      changePercent: stock.changePercent || 0,
      volume: stock.volume || 0,
      high: stock.high || stock.price || 0,
      low: stock.low || stock.price || 0,
      open: stock.open || stock.price || 0,
      close: stock.close || stock.price || 0,
      timestamp: Date.now(),
    }));
  } catch (error) {
    console.error('Error fetching multiple stocks:', error);
    return [];
  }
};

// Fetch index data
export const fetchIndexData = async (symbol: string): Promise<IndexQuote | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/index/${symbol}`);
    if (!response.ok) throw new Error('Failed to fetch index data');
    const data = await response.json();
    return {
      symbol: data.symbol || symbol,
      price: data.price || 0,
      change: data.change || 0,
      changePercent: data.changePercent || 0,
      timestamp: Date.now(),
    };
  } catch (error) {
    console.error(`Error fetching index data for ${symbol}:`, error);
    return null;
  }
};

// Fetch historical candlestick data
export const fetchCandlestickData = async (
  symbol: string,
  period: string = '1d',
  interval: string = '1m'
): Promise<any[]> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/candles/${symbol}?period=${period}&interval=${interval}`
    );
    if (!response.ok) throw new Error('Failed to fetch candlestick data');
    const data = await response.json();
    return data.map((candle: any) => ({
      time: candle.time || candle.timestamp || Date.now() / 1000,
      open: candle.open || 0,
      high: candle.high || 0,
      low: candle.low || 0,
      close: candle.close || 0,
      volume: candle.volume || 0,
    }));
  } catch (error) {
    console.error(`Error fetching candlestick data for ${symbol}:`, error);
    return [];
  }
};



