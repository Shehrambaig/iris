/**
 * Hook for NASDAQ live stock data
 * Fetches live prices every 5 seconds
 */

import { useState, useEffect } from 'react';
import { fetchNasdaqStocks, getNasdaqStockBySymbol, type NasdaqStockData } from '../services/nasdaqService';

const UPDATE_INTERVAL = 5000; // 5 seconds

/**
 * Hook to get live stock data for all companies
 * Updates every 5 seconds
 */
export const useNasdaqLiveStocks = () => {
  const [stocks, setStocks] = useState<NasdaqStockData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        const data = await fetchNasdaqStocks();
        if (isMounted) {
          setStocks(data);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
          setLoading(false);
        }
      }
    };

    // Fetch immediately
    fetchData();

    // Then fetch every 5 seconds
    const interval = setInterval(fetchData, UPDATE_INTERVAL);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { stocks, loading, error };
};

/**
 * Hook to get live stock data for a specific symbol
 * Updates every 5 seconds
 */
export const useNasdaqLiveStock = (symbol: string) => {
  const { stocks, loading, error } = useNasdaqLiveStocks();
  const stock = getNasdaqStockBySymbol(stocks, symbol);

  return { stock, loading, error };
};
