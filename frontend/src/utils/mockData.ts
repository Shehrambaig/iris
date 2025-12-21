import type { CandleData, StockData, IndexData, NewsEvent, EarningsData, DividendData } from '../types';

// Generate initial historical candle data
export const generateInitialCandles = (count: number, basePrice: number = 177): CandleData[] => {
  const candles: CandleData[] = [];
  const now = Math.floor(Date.now() / 1000);
  const daySeconds = 24 * 60 * 60;

  let currentPrice = basePrice;

  for (let i = count; i >= 0; i--) {
    const time = now - (i * daySeconds);
    const volatility = basePrice * 0.02; // 2% daily volatility

    const open = currentPrice;
    const change = (Math.random() - 0.5) * volatility;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;

    candles.push({
      time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume: Math.floor(Math.random() * 50000000) + 100000000
    });

    currentPrice = close;
  }

  return candles;
};

// Generate a new candle based on the last price
export const generateNewCandle = (lastCandle: CandleData): CandleData => {
  const volatility = lastCandle.close * 0.001; // 0.1% volatility per second
  const change = (Math.random() - 0.48) * volatility; // Slight upward bias

  const close = lastCandle.close + change;
  const high = Math.max(lastCandle.close, close) + Math.random() * volatility * 0.3;
  const low = Math.min(lastCandle.close, close) - Math.random() * volatility * 0.3;

  return {
    time: Math.floor(Date.now() / 1000),
    open: Number(lastCandle.close.toFixed(2)),
    high: Number(high.toFixed(2)),
    low: Number(low.toFixed(2)),
    close: Number(close.toFixed(2)),
    volume: Math.floor(Math.random() * 1000000) + 500000
  };
};

// Mock indices data
export const getMockIndices = (): IndexData[] => [
  {
    symbol: 'SPX',
    name: 'S&P 500',
    price: 6849.08,
    change: 36.48,
    changePercent: 0.54
  },
  {
    symbol: 'NDQ',
    name: 'NASDAQ',
    price: 25434.89,
    change: 197.95,
    changePercent: 0.78
  },
  {
    symbol: 'DJI',
    name: 'Dow Jones',
    price: 47716.42,
    change: 289.30,
    changePercent: 0.61
  },
  {
    symbol: 'VIX',
    name: 'Volatility Index',
    price: 16.35,
    change: -0.86,
    changePercent: -5.00
  },
  {
    symbol: 'DXY',
    name: 'Dollar Index',
    price: 99.297,
    change: -0.180,
    changePercent: -0.18
  }
];

// Mock stocks data
export const getMockStocks = (): StockData[] => [
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    price: 278.85,
    change: 1.30,
    changePercent: 0.47
  },
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corporation',
    price: 177.00,
    change: -3.26,
    changePercent: -1.81
  }
];

// Update prices with small random changes
export const updatePrices = (data: (IndexData | StockData)[]): (IndexData | StockData)[] => {
  return data.map(item => {
    const volatility = item.price * 0.0005; // 0.05% volatility
    const change = (Math.random() - 0.5) * volatility;
    const newPrice = item.price + change;
    const newChange = newPrice - (item.price - item.change);
    const newChangePercent = (newChange / (newPrice - newChange)) * 100;

    return {
      ...item,
      price: Number(newPrice.toFixed(item.price > 100 ? 2 : 3)),
      change: Number(newChange.toFixed(2)),
      changePercent: Number(newChangePercent.toFixed(2))
    };
  });
};

// Mock news events
export const getMockNewsEvents = (): NewsEvent[] => [
  {
    time: Math.floor(Date.now() / 1000) - 3600 * 24,
    price: 182.08,
    title: 'Nvidia competes with Google in the AI chip market',
    content: 'Nvidia competes with Google in the AI chip market as Alphabet\'s Gemini 3 model gains investor attention, challenging Nvidia\'s top position alongside Microsoft and AMD.',
    source: 'Reuters',
    timestamp: '1 hour ago'
  },
  {
    time: Math.floor(Date.now() / 1000) - 3600 * 48,
    price: 186.58,
    title: 'Meta investment in Google chips affects Nvidia',
    content: 'Nvidia\'s shares experienced volatility following reports that Meta is in discussions to invest billions in Google\'s chips, affecting investor sentiment towards the semiconductor company.',
    source: 'Bloomberg',
    timestamp: '2 days ago'
  },
  {
    time: Math.floor(Date.now() / 1000) - 3600 * 72,
    price: 181.48,
    title: 'Norway wealth fund proposal on Microsoft',
    content: 'Norway\'s $2 trillion wealth fund, a major Nvidia stakeholder, supports a proposal at Microsoft\'s annual meeting for a report on risks in countries with human rights issues.',
    source: 'Financial Times',
    timestamp: '3 days ago'
  }
];

// Mock earnings data
export const getMockEarningsData = (): EarningsData => ({
  date: 'Wed 28 May \'25',
  periodEnding: 'Apr \'25',
  standardized: 0.763,
  reported: 0.81,
  estimate: 0.737,
  surprise: 0.073,
  surprisePercent: 9.89,
  revenue: {
    reported: '44.06B',
    estimate: '43.33B',
    surprise: '727.84M',
    surprisePercent: 1.68
  }
});

// Mock dividend data
export const getMockDividendData = (): DividendData => ({
  exDividendDate: 'Wed 11 Jun \'25',
  amount: 0.01,
  paymentDate: 'Thu 03 Jul \'25'
});

// Mock latest updates
export const getMockLatestUpdates = () => [
  {
    title: 'Nvidia competes with Google in the AI chip market',
    content: 'Nvidia competes with Google in the AI chip market as Alphabet\'s Gemini 3 model gains investor attention, challenging Nvidia\'s top position alongside Microsoft and AMD.',
    timestamp: '1 hour ago',
    source: 'Reuters'
  },
  {
    title: 'Meta investment discussions',
    content: 'Nvidia\'s shares experienced volatility following reports that Meta is in discussions to invest billions in Google\'s chips, affecting investor sentiment towards the semiconductor company.',
    timestamp: '1 hour ago',
    source: 'Bloomberg'
  },
  {
    title: 'Norway wealth fund proposal',
    content: 'Norway\'s $2 trillion wealth fund, a major Nvidia stakeholder, supports a proposal at Microsoft\'s annual meeting for a report on risks in countries with human rights issues.',
    timestamp: '1 hour ago',
    source: 'Financial Times'
  }
];
