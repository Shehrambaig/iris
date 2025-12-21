import { X } from 'lucide-react';
import type { EarningsData, DividendData } from '../types';

interface EarningsOverlayProps {
  data: EarningsData;
  position: { x: number; y: number };
  onClose: () => void;
}

export const EarningsOverlay = ({ data, position, onClose }: EarningsOverlayProps) => {
  return (
    <div
      className="fixed z-50 bg-tradingview-panel border border-tradingview-border rounded-lg shadow-2xl p-4 w-80"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)'
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <span className="text-sm">📊</span>
          </div>
          <h3 className="text-base font-semibold text-tradingview-text">
            Earnings & Revenue
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-gray-400">Date</span>
            <div className="text-tradingview-text font-medium mt-1">{data.date}</div>
          </div>
          <div>
            <span className="text-gray-400">Period Ending</span>
            <div className="text-tradingview-text font-medium mt-1">{data.periodEnding}</div>
          </div>
        </div>

        <div className="border-t border-tradingview-border pt-3">
          <div className="text-xs text-gray-400 uppercase mb-2">Earnings</div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Standardized</span>
              <span className="text-tradingview-text font-medium">{data.standardized}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Reported</span>
              <span className="text-tradingview-text font-medium">{data.reported}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Estimate</span>
              <span className="text-tradingview-text font-medium">{data.estimate}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Surprise</span>
              <span className="text-tradingview-green font-medium">
                {data.surprise} ({data.surprisePercent}%)
              </span>
            </div>
          </div>
        </div>

        <div className="border-t border-tradingview-border pt-3">
          <div className="text-xs text-gray-400 uppercase mb-2">Revenue</div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Reported</span>
              <span className="text-tradingview-text font-medium">{data.revenue.reported}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Estimate</span>
              <span className="text-tradingview-text font-medium">{data.revenue.estimate}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Surprise</span>
              <span className="text-tradingview-green font-medium">
                {data.revenue.surprise} ({data.revenue.surprisePercent}%)
              </span>
            </div>
          </div>
        </div>

        <button className="w-full text-xs text-blue-400 hover:text-blue-300 transition-colors mt-2">
          More NVDA financials
        </button>
      </div>
    </div>
  );
};

interface DividendsOverlayProps {
  data: DividendData;
  position: { x: number; y: number };
  onClose: () => void;
}

export const DividendsOverlay = ({ data, position, onClose }: DividendsOverlayProps) => {
  return (
    <div
      className="fixed z-50 bg-tradingview-panel border border-tradingview-border rounded-lg shadow-2xl p-4 w-72"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)'
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
            <span className="text-sm">💰</span>
          </div>
          <h3 className="text-base font-semibold text-tradingview-text">Dividends</h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Ex-dividend date</span>
          <span className="text-tradingview-text font-medium">{data.exDividendDate}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Amount</span>
          <span className="text-tradingview-text font-medium">{data.amount}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Payment date</span>
          <span className="text-tradingview-text font-medium">{data.paymentDate}</span>
        </div>

        <button className="w-full text-xs text-blue-400 hover:text-blue-300 transition-colors mt-2">
          More NVDA dividends
        </button>
      </div>
    </div>
  );
};

interface LatestUpdatesOverlayProps {
  updates: Array<{
    title: string;
    content: string;
    timestamp: string;
    source: string;
  }>;
  position: { x: number; y: number };
  onClose: () => void;
}

export const LatestUpdatesOverlay = ({ updates, position, onClose }: LatestUpdatesOverlayProps) => {
  return (
    <div
      className="fixed z-50 bg-tradingview-panel border border-tradingview-border rounded-lg shadow-2xl p-4 w-96"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)'
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
            <span className="text-sm">⚡</span>
          </div>
          <h3 className="text-base font-semibold text-tradingview-text">Latest updates</h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {updates.map((update, index) => (
          <div
            key={index}
            className="p-3 bg-tradingview-bg rounded border border-tradingview-border hover:border-gray-600 transition-colors cursor-pointer"
          >
            <h4 className="text-sm font-medium text-tradingview-text mb-1">
              {update.title}
            </h4>
            <p className="text-xs text-gray-400 mb-2 line-clamp-2">{update.content}</p>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{update.timestamp}</span>
              <span>{update.source}</span>
            </div>
          </div>
        ))}

        <button className="w-full text-xs text-blue-400 hover:text-blue-300 transition-colors mt-2">
          More events
        </button>
      </div>
    </div>
  );
};
