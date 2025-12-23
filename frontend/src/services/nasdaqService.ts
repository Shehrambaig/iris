/**
 * NASDAQ API Service
 * Fetches live stock prices from NASDAQ API every 5 seconds via backend proxy
 */
import { API_BASE } from './api';

// Use backend proxy to avoid CORS issues
const BACKEND_API_URL = `${API_BASE}/api/nasdaq/watchlist`;

export interface NasdaqStockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
}

interface NasdaqApiResponse {
  data: {
    rows: Array<{
      symbol: string;
      name: string;
      lastSale: string;
      change: string;
      pctChange: string;
      volume: string;
    }>;
  };
  status: {
    rCode: number;
  };
}

/**
 * Parse price string like "$180.99" to number 180.99
 */
const parsePrice = (priceStr: string): number => {
  return parseFloat(priceStr.replace('$', '').replace(',', ''));
};

/**
 * Parse change string like "+6.85" to number 6.85
 */
const parseChange = (changeStr: string): number => {
  return parseFloat(changeStr.replace('+', ''));
};

/**
 * Parse percent change string like "+3.93%" to number 3.93
 */
const parsePercentChange = (pctStr: string): number => {
  return parseFloat(pctStr.replace('+', '').replace('%', ''));
};

/**
 * Fetch live stock data from NASDAQ API via backend proxy
 */
export const fetchNasdaqStocks = async (): Promise<NasdaqStockData[]> => {
  try {
    const response = await fetch(BACKEND_API_URL);

    if (!response.ok) {
      throw new Error(`Backend proxy error: ${response.status}`);
    }

    const data: NasdaqApiResponse = await response.json();

    if (data.status.rCode !== 200 || !data.data?.rows) {
      throw new Error('Invalid NASDAQ API response');
    }

    return data.data.rows.map(row => ({
      symbol: row.symbol,
      name: row.name,
      price: parsePrice(row.lastSale),
      change: parseChange(row.change),
      changePercent: parsePercentChange(row.pctChange),
      volume: row.volume,
    }));
  } catch (error) {
    console.error('[NASDAQ Service] Error fetching stock data:', error);
    throw error;
  }
};

/**
 * Get a single stock by symbol from the NASDAQ data
 */
export const getNasdaqStockBySymbol = (
  stocks: NasdaqStockData[],
  symbol: string
): NasdaqStockData | undefined => {
  return stocks.find(s => s.symbol.toUpperCase() === symbol.toUpperCase());
};
