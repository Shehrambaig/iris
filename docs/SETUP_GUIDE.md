# Setup Guide - Live Stock Data & Sentiment Analysis

## What's Been Added

### 1. **Improved Logos**
- ✅ Apple logo for AAPL
- ✅ Nvidia eye logo for NVDA  
- ✅ Dollar sign ($) for DXY
- ✅ Stylized letters for indices (S&P, N, D, V)

### 2. **Real-Time Data Integration**
Created services and hooks to fetch live stock data:

**Files Created:**
- `src/services/stockDataService.ts` - Fetches stock/index data from backend
- `src/services/newsService.ts` - Fetches and analyzes news
- `src/services/sentimentAgent.ts` - Sentiment analysis agent
- `src/hooks/useLiveStockData.ts` - React hooks for live data
- `backend-example.py` - Python FastAPI backend example

### 3. **Sentiment Analysis Agent**
The `SentimentAgent` class:
- Monitors price movements
- Fetches news related to the stock
- Analyzes sentiment of news articles
- Correlates news with price movements
- Detects significant price events (>0.5% change)

### 4. **News Correlation**
- Fetches news from internet when events happen
- Analyzes sentiment (positive/negative/neutral)
- Correlates news with price movements
- Shows which news might have caused price changes

## Setup Instructions

### Step 1: Set Up Backend

**Option A: Python Backend (Recommended)**

1. Install Python dependencies:
```bash
pip install fastapi uvicorn yfinance requests beautifulsoup4
```

2. For advanced sentiment analysis (optional):
```bash
pip install transformers torch
```

3. Run the backend:
```bash
python backend-example.py
# Or:
uvicorn backend-example:app --reload --port 8000
```

**Option B: Node.js Backend**

Create a backend using Express.js that calls yfinance or Nasdaq API.

### Step 2: Configure Frontend

1. Create `.env` file in project root:
```
VITE_API_BASE_URL=http://localhost:8000
```

2. The frontend will automatically:
   - Try to fetch live data from backend
   - Fall back to mock data if backend is unavailable
   - Update every second when live data is available

### Step 3: Test the Integration

1. Start the backend (if using Python)
2. Start the frontend: `npm run dev`
3. The app will automatically use live data if backend is running
4. Check browser console for any connection errors

## How It Works

### Live Data Flow:
1. Frontend hooks (`useLiveStockData`, `useLiveIndices`, `useLiveStocks`) fetch data every second
2. Backend API endpoints provide real-time stock data using yfinance
3. If backend is unavailable, app gracefully falls back to mock data

### Sentiment Analysis Flow:
1. When price moves significantly (>0.5%), `SentimentAgent` is triggered
2. Agent fetches recent news for the stock
3. Each news article is analyzed for sentiment
4. News is correlated with the price movement
5. Results are stored in `priceEvents` state

### News Correlation:
- News is fetched when price events occur
- Sentiment analysis determines if news is positive/negative
- Price movements are matched with news timestamps
- You can see which news might have caused price changes

## API Endpoints Required

Your backend should provide:

- `GET /api/stock/{symbol}` - Single stock quote
- `POST /api/stocks` - Multiple stocks (body: `{symbols: ["AAPL", "NVDA"]}`)
- `GET /api/index/{symbol}` - Index data (SPX, NDQ, DJI, VIX, DXY)
- `GET /api/candles/{symbol}?period=6mo&interval=1d` - Historical candlestick data
- `GET /api/news/{symbol}?limit=10` - News articles
- `POST /api/sentiment/analyze` - Sentiment analysis (body: `{text: "..."}`)

## Features

✅ **Live Price Updates** - Updates every second from yfinance/Nasdaq  
✅ **Sentiment Analysis** - Analyzes news sentiment automatically  
✅ **News Correlation** - Links news to price movements  
✅ **Event Detection** - Detects significant price movements  
✅ **Graceful Fallback** - Uses mock data if backend unavailable  

## Next Steps

1. Set up the backend using `backend-example.py`
2. Get a NewsAPI key (optional, for better news) from newsapi.org
3. Customize sentiment analysis model if needed
4. Add more stocks/indices as needed

The frontend is ready and will automatically use live data when the backend is available!



