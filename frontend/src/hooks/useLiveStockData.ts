// Hook for live stock data updates
import { useState, useEffect, useCallback } from 'react';
import { fetchStockData, fetchMultipleStocks, fetchIndexData, fetchCandlestickData, type StockQuote, type IndexQuote } from '../services/stockDataService';
import { SentimentAgent, type PriceEvent } from '../services/sentimentAgent';
import type { StockData, IndexData, CandleData } from '../types';

const UPDATE_INTERVAL = 30000; // Update every 30 seconds (reduced to avoid rate limiting)

export const useLiveStockData = (symbol: string) => {
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [candleData, setCandleData] = useState<CandleData[]>([]);
  const [priceEvents, setPriceEvents] = useState<PriceEvent[]>([]);
  const [sentimentAgent] = useState(() => new SentimentAgent(symbol));

  // Fetch initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const stock = await fetchStockData(symbol);
        if (stock) {
          setStockData({
            symbol: stock.symbol,
            name: getStockName(symbol),
            price: stock.price,
            change: stock.change,
            changePercent: stock.changePercent,
            volume: formatVolume(stock.volume),
          });
        }

        // Load candlestick data
        const candles = await fetchCandlestickData(symbol, '6mo', '1d');
        if (candles.length > 0) {
          setCandleData(candles);
        }
      } catch (error) {
        // Silently fail - will use mock data
        console.log('Live data not available, using mock data');
      }
    };

    loadInitialData();
  }, [symbol]);

  // Live updates
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const stock = await fetchStockData(symbol);
        if (stock && stockData) {
          const newStockData: StockData = {
            symbol: stock.symbol,
            name: stockData.name,
            price: stock.price,
            change: stock.change,
            changePercent: stock.changePercent,
            volume: formatVolume(stock.volume),
          };

          setStockData(newStockData);

          // Monitor price movement with sentiment agent
          try {
            const event = await sentimentAgent.monitorPriceMovement(
              stock.price,
              Date.now()
            );

            if (event) {
              setPriceEvents((prev) => [event, ...prev].slice(0, 10)); // Keep last 10 events
            }
          } catch (error) {
            // Sentiment analysis failed, continue without it
          }

          // Update latest candle
          setCandleData((prev) => {
            if (prev.length === 0) return prev;
            const newCandle: CandleData = {
              time: Math.floor(Date.now() / 1000),
              open: stock.open,
              high: stock.high,
              low: stock.low,
              close: stock.price,
              volume: stock.volume,
            };
            return [...prev.slice(-179), newCandle];
          });
        }
      } catch (error) {
        // Silently fail - will continue with existing data
      }
    }, UPDATE_INTERVAL);

    return () => clearInterval(interval);
  }, [symbol, stockData, sentimentAgent]);

  return { stockData, candleData, priceEvents };
};

export const useLiveIndices = (symbols: string[]) => {
  const [indices, setIndices] = useState<IndexData[]>([]);

  useEffect(() => {
    const loadIndices = async () => {
      try {
        const indexData = await Promise.all(
          symbols.map(async (symbol) => {
            try {
              const data = await fetchIndexData(symbol);
              if (data) {
                return {
                  symbol: data.symbol,
                  name: getIndexName(data.symbol),
                  price: data.price,
                  change: data.change,
                  changePercent: data.changePercent,
                };
              }
            } catch (error) {
              // Skip failed fetches
            }
            return null;
          })
        );
        const validData = indexData.filter((d): d is IndexData => d !== null);
        if (validData.length > 0) {
          setIndices(validData);
        }
      } catch (error) {
        // Silently fail
      }
    };

    loadIndices();

    const interval = setInterval(loadIndices, UPDATE_INTERVAL);
    return () => clearInterval(interval);
  }, [symbols.join(',')]);

  return indices;
};

export const useLiveStocks = (symbols: string[]) => {
  const [stocks, setStocks] = useState<StockData[]>([]);

  useEffect(() => {
    const loadStocks = async () => {
      // TEMPORARILY DISABLED due to Yahoo Finance rate limiting blocking the backend
      // Return empty array to avoid blocking the news API
      console.log('[useLiveStocks] Skipping stock data fetch to avoid blocking backend');
      return;

      /* ORIGINAL CODE - uncomment when Yahoo Finance issue is resolved
      try {
        const stockData = await fetchMultipleStocks(symbols);
        if (stockData.length > 0) {
          setStocks(
            stockData.map((stock) => ({
              symbol: stock.symbol,
              name: getStockName(stock.symbol),
              price: stock.price,
              change: stock.change,
              changePercent: stock.changePercent,
              volume: formatVolume(stock.volume),
            }))
          );
        }
      } catch (error) {
        // Silently fail
      }
      */
    };

    loadStocks();

    // Commenting out interval to prevent repeated attempts
    // const interval = setInterval(loadStocks, UPDATE_INTERVAL);
    // return () => clearInterval(interval);
  }, [symbols.join(',')]);

  return stocks;
};

// Helper functions
const getStockName = (symbol: string): string => {
  const names: Record<string, string> = {
    AAPL: 'Apple Inc.',
    NVDA: 'NVIDIA Corporation',
  };
  return names[symbol] || symbol;
};

const getIndexName = (symbol: string): string => {
  const names: Record<string, string> = {
    SPX: 'S&P 500',
    NDQ: 'NASDAQ',
    DJI: 'Dow Jones',
    VIX: 'Volatility Index',
    DXY: 'Dollar Index',
  };
  return names[symbol] || symbol;
};

const formatVolume = (volume: number): string => {
  if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
  if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
  if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
  return volume.toString();
};

