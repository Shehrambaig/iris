export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: string;
}

export interface IndexData extends StockData {
  icon?: string;
}

export interface NewsEvent {
  time: number;
  price: number;
  title: string;
  content: string;
  source: string;
  timestamp: string;
}

export interface EarningsData {
  date: string;
  periodEnding: string;
  standardized: number;
  reported: number;
  estimate: number;
  surprise: number;
  surprisePercent: number;
  revenue: {
    reported: string;
    estimate: string;
    surprise: string;
    surprisePercent: number;
  };
}

export interface DividendData {
  exDividendDate: string;
  amount: number;
  paymentDate: string;
}

export interface OverlayType {
  type: 'earnings' | 'dividends' | 'news';
  position: { x: number; y: number };
}
