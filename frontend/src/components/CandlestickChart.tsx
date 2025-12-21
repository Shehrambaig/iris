import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { IChartApi, CandlestickData, Time, SeriesMarker } from 'lightweight-charts';
import type { CandleData, NewsEvent } from '../types';

interface CandlestickChartProps {
  data: CandleData[];
  newsEvents: NewsEvent[];
  onNewsClick: (news: NewsEvent, position: { x: number; y: number }) => void;
}

interface EventMarker {
  time: number;
  price: number;
  type: 'earnings' | 'dividends' | 'news';
  title: string;
  x: number;
  y: number;
}

export const CandlestickChart = ({ data, newsEvents, onNewsClick }: CandlestickChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const [eventMarkers, setEventMarkers] = useState<EventMarker[]>([]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0a0e27' },
        textColor: '#D1D4DC',
      },
      grid: {
        vertLines: { color: '#1e222d', visible: true },
        horzLines: { color: '#1e222d', visible: true },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      rightPriceScale: {
        borderColor: '#1e222d',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#1e222d',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#758696',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: '#758696',
          width: 1,
          style: 2,
        },
      },
      watermark: {
        visible: false,
      },
    });

    // Add candlestick series (v5 API)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26A69A',
      downColor: '#EF5350',
      borderUpColor: '#26A69A',
      borderDownColor: '#EF5350',
      wickUpColor: '#26A69A',
      wickDownColor: '#EF5350',
    });

    // Add volume series (v5 API)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [newsEvents, onNewsClick]);

  // Update data
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

    const candleData: CandlestickData<Time>[] = data.map(d => ({
      time: d.time as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const volumeData = data.map(d => ({
      time: d.time as Time,
      value: d.volume || 0,
      color: d.close >= d.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  // News markers removed per user request
  // useEffect(() => {
  //   if (!candleSeriesRef.current || newsEvents.length === 0) return;
  //   try {
  //     const markers: SeriesMarker<Time>[] = newsEvents.map(news => ({
  //       time: news.time as Time,
  //       position: 'aboveBar' as const,
  //       color: '#2196F3',
  //       shape: 'circle' as const,
  //       text: 'N',
  //       size: 1,
  //     }));
  //     candleSeriesRef.current.setMarkers(markers);
  //   } catch (error) {
  //     console.log('Markers not supported:', error);
  //   }
  // }, [newsEvents]);

  // Calculate event marker positions for overlay - position on actual candles
  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current || newsEvents.length === 0 || data.length === 0) return;

    const updateMarkerPositions = () => {
      try {
        const timeScale = chartRef.current!.timeScale();
        const priceScale = candleSeriesRef.current!.priceScale();

        const markers: EventMarker[] = [];

        for (const event of newsEvents) {
          // Find the candle that corresponds to this event time
          const candle = data.find(d => d.time === event.time);

          if (candle) {
            // Get x position from time
            const x = timeScale.timeToCoordinate(event.time as Time);

            // Position marker at the HIGH of the candle (above the candle)
            const y = candleSeriesRef.current!.priceToCoordinate(candle.high);

            if (x !== null && y !== null) {
              markers.push({
                time: event.time,
                price: candle.close, // Show close price for the candle
                type: 'news',
                title: event.title,
                x: x,
                y: y - 20, // Position 20px above the high point
              });
            }
          }
        }

        setEventMarkers(markers);
      } catch (error) {
        console.log('Error calculating marker positions:', error);
      }
    };

    // Update positions on chart scroll/zoom
    const timeScale = chartRef.current.timeScale();
    timeScale.subscribeVisibleLogicalRangeChange(updateMarkerPositions);

    // Initial position calculation
    updateMarkerPositions();

    return () => {
      try {
        timeScale.unsubscribeVisibleLogicalRangeChange(updateMarkerPositions);
      } catch (e) {
        // Ignore errors during cleanup
      }
    };
  }, [newsEvents, data]);

  const getEventIcon = (type: 'earnings' | 'dividends' | 'news') => {
    switch (type) {
      case 'earnings':
        return (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 3v18h18" />
            <path d="M18 17V9" />
            <path d="M13 17V5" />
            <path d="M8 17v-3" />
          </svg>
        );
      case 'dividends':
        return (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v12M9 9h6M9 15h6" />
          </svg>
        );
      case 'news':
      default:
        return (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
            <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
          </svg>
        );
    }
  };

  const getEventColor = (type: 'earnings' | 'dividends' | 'news') => {
    switch (type) {
      case 'earnings':
        return 'bg-blue-500/20 hover:bg-blue-500/30 border-blue-500/40 text-blue-400 hover:text-blue-300';
      case 'dividends':
        return 'bg-emerald-500/20 hover:bg-emerald-500/30 border-emerald-500/40 text-emerald-400 hover:text-emerald-300';
      case 'news':
      default:
        return 'bg-purple-500/20 hover:bg-purple-500/30 border-purple-500/40 text-purple-400 hover:text-purple-300';
    }
  };

  return (
    <div className="relative w-full h-full">
      <div ref={chartContainerRef} className="w-full h-full" />

      {/* Event markers overlay */}
      {eventMarkers.map((marker, index) => (
        <button
          key={`${marker.time}-${index}`}
          className={`absolute p-1.5 rounded-full cursor-pointer transition-all hover:scale-125 border shadow-lg backdrop-blur-sm z-20 ${getEventColor(marker.type)}`}
          style={{
            left: `${marker.x}px`,
            top: `${marker.y}px`,
            transform: 'translate(-50%, -50%)',
          }}
          onClick={(e) => {
            const newsEvent = newsEvents.find(n => n.time === marker.time);
            if (newsEvent) {
              onNewsClick(newsEvent, { x: e.clientX, y: e.clientY });
            }
          }}
          title={`${marker.title} - Price: $${marker.price.toFixed(2)}`}
        >
          {getEventIcon(marker.type)}

          {/* Price label */}
          <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-[#0a0e27]/95 border border-[#1e222d] rounded px-2 py-1 text-[10px] font-medium text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            ${marker.price.toFixed(2)}
          </div>
        </button>
      ))}
    </div>
  );
};
