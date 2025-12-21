import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { CandlestickChart } from '../components/CandlestickChart';
import { RightSidebar } from '../components/RightSidebar';
import { TopBar } from '../components/TopBar';
import { EarningsOverlay, DividendsOverlay, LatestUpdatesOverlay } from '../components/Overlays';
import {
  generateInitialCandles,
  generateNewCandle,
  getMockIndices,
  getMockStocks,
  updatePrices,
  getMockNewsEvents,
  getMockEarningsData,
  getMockDividendData,
  getMockLatestUpdates,
} from '../utils/mockData';
import { useLiveStockData, useLiveIndices } from '../hooks/useLiveStockData';
import { useNasdaqLiveStocks } from '../hooks/useNasdaqLiveData';
import type { CandleData, IndexData, StockData, NewsEvent, OverlayType } from '../types';

export const GraphPage = () => {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();

  // State
  const [selectedSymbol, setSelectedSymbol] = useState<string>(urlSymbol || 'NVDA');
  const [newsEvents] = useState<NewsEvent[]>(getMockNewsEvents());
  const [activeOverlay, setActiveOverlay] = useState<OverlayType | null>(null);
  const [overlayPosition, setOverlayPosition] = useState({ x: 0, y: 0 });
  const [timeframe, setTimeframe] = useState('1D');
  const [currentTime, setCurrentTime] = useState(new Date());

  // Live data hooks
  const liveStockData = useLiveStockData(selectedSymbol);
  const liveIndices = useLiveIndices(['SPX', 'NDQ', 'DJI', 'VIX', 'DXY']);
  // Use NASDAQ API for live stock prices (updates every 5 seconds)
  const { stocks: nasdaqStocks, loading: loadingNasdaq } = useNasdaqLiveStocks();

  const [candleDataState, setCandleDataState] = useState<CandleData[]>([]);
  const [indices, setIndices] = useState<IndexData[]>([]);
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);

  // Initialize with mock data
  useEffect(() => {
    const initialCandles = generateInitialCandles(180, 177);
    setCandleDataState(initialCandles);

    const initialIndices = getMockIndices();
    const initialStocks = getMockStocks();

    setIndices(initialIndices);
    setStocks(initialStocks);
    setSelectedStock(initialStocks[1]); // NVDA
  }, []);

  // Use live data if available
  useEffect(() => {
    if (liveStockData.stockData) {
      setSelectedStock(liveStockData.stockData);
    }
    if (liveStockData.candleData.length > 0) {
      setCandleDataState(liveStockData.candleData);
    }
  }, [liveStockData]);

  useEffect(() => {
    if (liveIndices.length > 0) {
      setIndices(liveIndices);
    }
  }, [liveIndices]);

  // Update stocks with NASDAQ live data AND update candlestick chart
  useEffect(() => {
    if (nasdaqStocks.length > 0) {
      const mappedStocks: StockData[] = nasdaqStocks.map(stock => ({
        symbol: stock.symbol,
        name: stock.name,
        price: stock.price,
        change: stock.change,
        changePercent: stock.changePercent,
        volume: stock.volume,
      }));

      setStocks(mappedStocks);

      // Update selected stock if it matches
      const symbolToFind = selectedSymbol === 'GOOGL' ? 'GOOG' : selectedSymbol;
      const updated = mappedStocks.find((s) => s.symbol === symbolToFind);
      if (updated) {
        setSelectedStock(updated);

        // UPDATE CANDLESTICK CHART WITH LIVE PRICE
        setCandleDataState(prev => {
          if (prev.length === 0) return prev;

          const lastCandle = prev[prev.length - 1];
          const currentPrice = updated.price;

          // Update the last candle with live price
          const updatedCandle = {
            ...lastCandle,
            close: currentPrice,
            high: Math.max(lastCandle.high, currentPrice),
            low: Math.min(lastCandle.low, currentPrice),
          };

          return [...prev.slice(0, -1), updatedCandle];
        });
      }
    }
  }, [nasdaqStocks, selectedSymbol]);

  // Update current time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timeInterval);
  }, []);

  // Fallback: Live price updates with mock data (if live data not available)
  useEffect(() => {
    // Only use mock updates if live data is not available
    if (liveStockData.stockData) return;

    const interval = setInterval(() => {
      setCandleDataState((prev) => {
        if (prev.length === 0) return prev;
        const lastCandle = prev[prev.length - 1];
        const newCandle = generateNewCandle(lastCandle);
        return [...prev.slice(-179), newCandle];
      });

      setIndices((prev) => updatePrices(prev) as IndexData[]);
      setStocks((prev) => {
        const updated = updatePrices(prev) as StockData[];
        if (selectedStock) {
          const updatedSelected = updated.find((s) => s.symbol === selectedStock.symbol);
          if (updatedSelected) {
            setSelectedStock(updatedSelected);
          }
        }
        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [selectedStock, liveStockData.stockData]);

  // Use the appropriate candle data
  const activeCandleData = liveStockData.candleData.length > 0 ? liveStockData.candleData : candleDataState;

  // Handle news click from chart markers
  const handleNewsClick = useCallback((news: NewsEvent, position: { x: number; y: number }) => {
    setActiveOverlay({ type: 'news', position });
    setOverlayPosition(position);
  }, []);

  // Handle overlay button clicks (bottom dots)
  const handleOverlayButtonClick = (
    type: 'earnings' | 'dividends' | 'news',
    event: React.MouseEvent
  ) => {
    // Position overlay near bottom-left of chart area
    const position = {
      x: window.innerWidth * 0.25, // Left quarter of screen
      y: window.innerHeight * 0.65, // Lower portion
    };
    setActiveOverlay({ type, position });
    setOverlayPosition(position);
  };

  if (!selectedStock) {
    return (
      <div className="w-screen h-screen bg-gradient-to-b from-[#0a0e27] to-[#0f1420] flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen bg-gradient-to-b from-[#0a0e27] to-[#0f1420] flex flex-col overflow-hidden">
      {/* Top Bar */}
      <TopBar
        symbol={selectedStock.symbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        selectedStock={selectedStock}
        indices={indices}
      />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chart Area */}
        <div className="flex-1 relative">
          <CandlestickChart
            data={activeCandleData}
            newsEvents={newsEvents}
            onNewsClick={handleNewsClick}
          />

          {/* Bottom Overlay Buttons (Earnings, Dividends, News) */}
          <div className="absolute bottom-12 left-1/2 transform -translate-x-1/2 flex items-center gap-2 bg-gradient-to-r from-[#0a0e27]/95 via-[#0d1128]/95 to-[#0a0e27]/95 backdrop-blur-sm border border-[#1e222d] rounded-full px-4 py-2 shadow-2xl z-10">
            <button
              onClick={(e) => handleOverlayButtonClick('earnings', e)}
              className="group relative p-2 rounded-full bg-blue-500/20 hover:bg-blue-500/30 cursor-pointer transition-all hover:scale-110 border border-blue-500/40"
              title="Earnings & Revenue"
            >
              <svg className="w-4 h-4 text-blue-400 group-hover:text-blue-300 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 3v18h18" />
                <path d="M18 17V9" />
                <path d="M13 17V5" />
                <path d="M8 17v-3" />
              </svg>
            </button>
            <button
              onClick={(e) => handleOverlayButtonClick('dividends', e)}
              className="group relative p-2 rounded-full bg-emerald-500/20 hover:bg-emerald-500/30 cursor-pointer transition-all hover:scale-110 border border-emerald-500/40"
              title="Dividends"
            >
              <svg className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v12M9 9h6M9 15h6" />
              </svg>
            </button>
            <button
              onClick={(e) => handleOverlayButtonClick('news', e)}
              className="group relative p-2 rounded-full bg-purple-500/20 hover:bg-purple-500/30 cursor-pointer transition-all hover:scale-110 border border-purple-500/40"
              title="Latest Updates"
            >
              <svg className="w-4 h-4 text-purple-400 group-hover:text-purple-300 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              </svg>
            </button>
          </div>
        </div>

        {/* Right Sidebar */}
        <RightSidebar
          indices={indices}
          stocks={stocks}
          selectedStock={selectedStock}
          onStockSelect={(symbol) => {
            setSelectedSymbol(symbol);
            const stock = stocks.find((s) => s.symbol === symbol);
            if (stock) setSelectedStock(stock);
          }}
        />
      </div>

      {/* Overlays */}
      {activeOverlay?.type === 'earnings' && (
        <EarningsOverlay
          data={getMockEarningsData()}
          position={overlayPosition}
          onClose={() => setActiveOverlay(null)}
        />
      )}
      {activeOverlay?.type === 'dividends' && (
        <DividendsOverlay
          data={getMockDividendData()}
          position={overlayPosition}
          onClose={() => setActiveOverlay(null)}
        />
      )}
      {activeOverlay?.type === 'news' && (
        <LatestUpdatesOverlay
          updates={getMockLatestUpdates()}
          position={overlayPosition}
          onClose={() => setActiveOverlay(null)}
        />
      )}

    </div>
  );
};
